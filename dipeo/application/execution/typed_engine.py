"""Refactored typed execution engine using unified ExecutionContext."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.scheduler import NodeScheduler
from dipeo.application.execution.typed_execution_context import TypedExecutionContext
from dipeo.config import get_settings
from dipeo.diagram_generated import ExecutionState, NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.events.unified_ports import EventBus

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

logger = logging.getLogger(__name__)


class TypedExecutionEngine:
    """Refactored execution engine with clean separation of concerns."""

    def __init__(
        self,
        service_registry: "ServiceRegistry",
        event_bus: EventBus | None = None,
    ):
        self.service_registry = service_registry
        self._settings = get_settings()
        self._managed_event_bus = False
        self._scheduler: NodeScheduler | None = None

        if not event_bus:
            from dipeo.infrastructure.events.adapters import InMemoryEventBus

            self.event_bus = InMemoryEventBus()
            self._managed_event_bus = True
        else:
            self.event_bus = event_bus

    async def execute(
        self,
        diagram: ExecutableDiagram,
        execution_state: ExecutionState,
        options: dict[str, Any],
        container: Optional["Container"] = None,
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        if self._managed_event_bus:
            await self.event_bus.start()

        context = None
        log_handler = None
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

            await context.events.emit_execution_started()

            from dipeo.application.registry import ServiceKey

            self.service_registry.register(ServiceKey("diagram"), diagram)
            self.service_registry.register(
                ServiceKey("execution_context"), {"interactive_handler": interactive_handler}
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
                results = await self._execute_nodes(ready_nodes, context)

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

            await context.events.emit_execution_completed(
                status=Status.COMPLETED, total_steps=step_count, execution_path=execution_path
            )

            # Explicitly update execution status to ensure it's marked as inactive
            from dipeo.application.registry.keys import STATE_STORE

            state_store = self.service_registry.get(STATE_STORE)
            if state_store:
                try:
                    await state_store.update_status(
                        execution_id=str(context.execution_id),
                        status=Status.COMPLETED,
                        error=None,
                    )
                except Exception as e:
                    logger.warning(f"Failed to update execution status: {e}")

            yield {
                "type": "execution_complete",
                "total_steps": step_count,
                "execution_path": execution_path,
            }

        except Exception as e:
            from dipeo.diagram_generated import Status

            if context:
                await context.events.emit_execution_error(e)

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

            if self._managed_event_bus:
                await self.event_bus.stop()

    async def _execute_nodes(
        self, nodes: list[ExecutableNode], context: TypedExecutionContext
    ) -> dict[str, dict[str, Any]]:
        max_concurrent = 20

        if len(nodes) == 1:
            node = nodes[0]
            result = await self._execute_single_node(node, context)
            return {str(node.id): result}

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(node: ExecutableNode) -> tuple[str, dict[str, Any]]:
            async with semaphore:
                result = await self._execute_single_node(node, context)
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
        self, node: ExecutableNode, context: TypedExecutionContext
    ) -> dict[str, Any]:
        node_id = node.id
        start_time = time.time()
        epoch = context.current_epoch()

        if self._scheduler:
            self._scheduler.mark_node_running(node_id, epoch)

        await self._emit_node_started(context, node)

        try:
            if await self._should_skip_max_iteration(node, context):
                return await self._handle_max_iteration_reached(node, context)

            output = await self._execute_node_handler(node, context)

            from dipeo.diagram_generated import NodeType

            if node.type != NodeType.CONDITION and output:
                outputs = {"default": output} if not isinstance(output, dict) else output
                context.emit_outputs_as_tokens(node_id, outputs, epoch)

            duration_ms = (time.time() - start_time) * 1000
            llm_usage = self._extract_llm_usage(output)

            await self._handle_node_completion(node, output, context)

            if self._scheduler:
                self._scheduler.mark_node_complete(node_id, epoch)

            await self._emit_node_completed(
                context, node, output, duration_ms, start_time, llm_usage
            )

            return self._format_node_result(output)

        except Exception as e:
            if self._scheduler:
                self._scheduler.mark_node_complete(node_id, epoch)
            await self._handle_node_failure(context, node, e)
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
        self, node: ExecutableNode, context: TypedExecutionContext
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

        await context.events.emit_node_status_changed(node_id, Status.COMPLETED)
        await context.events.emit_node_completed(node, None, current_count)

        return {"value": "", "status": "MAXITER_REACHED"}

    async def _execute_node_handler(
        self, node: ExecutableNode, context: TypedExecutionContext
    ) -> Any:
        with context.executing_node(node.id):
            context.state.transition_to_running(node.id, context.current_epoch())

            from dipeo.diagram_generated import Status

            await context.events.emit_node_status_changed(node.id, Status.RUNNING)

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
                    usage_dict = llm_usage.model_dump()
                    logger.debug(f"[TypedEngine] Extracted LLM usage from envelope: {usage_dict}")
                    return usage_dict
                elif isinstance(llm_usage, dict):
                    logger.debug(f"[TypedEngine] Extracted LLM usage from envelope: {llm_usage}")
                    return llm_usage
        return None

    async def _emit_node_started(
        self, context: TypedExecutionContext, node: ExecutableNode
    ) -> None:
        await context.events.emit_node_started(node)

    async def _emit_node_completed(
        self,
        context: TypedExecutionContext,
        node: ExecutableNode,
        envelope: Any,
        duration_ms: float,
        start_time: float,
        llm_usage: dict | None,
    ) -> None:
        if hasattr(envelope, "meta") and isinstance(envelope.meta, dict):
            envelope.meta["execution_time_ms"] = duration_ms
            if llm_usage:
                envelope.meta["token_usage"] = llm_usage

        exec_count = context.state.get_node_execution_count(node.id)
        await context.events.emit_node_completed(node, envelope, exec_count)

    async def _handle_node_failure(
        self, context: TypedExecutionContext, node: ExecutableNode, error: Exception
    ) -> None:
        logger.error(f"Error executing node {node.id}: {error}", exc_info=True)
        context.state.transition_to_failed(node.id, str(error))

        from dipeo.diagram_generated import Status

        await context.events.emit_node_status_changed(node.id, Status.FAILED)
        await context.events.emit_node_error(node, error)

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
        from dipeo.application.execution.handler_factory import HandlerFactory

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
    ) -> None:
        context.state.transition_to_completed(node.id, envelope)

        from dipeo.diagram_generated import Status

        await context.events.emit_node_status_changed(node.id, Status.COMPLETED)
