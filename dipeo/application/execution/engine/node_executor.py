"""Node execution logic for the execution engine."""

import logging
import time
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.engine.helpers import (
    extract_llm_usage,
    format_node_result,
    get_handler,
)
from dipeo.config.base_logger import get_module_logger

if TYPE_CHECKING:
    from dipeo.application.execution.engine.context import TypedExecutionContext
    from dipeo.application.execution.engine.scheduler import NodeScheduler
    from dipeo.application.execution.events import EventPipeline
    from dipeo.domain.diagram.models.executable_diagram import ExecutableNode

logger = get_module_logger(__name__)


async def execute_single_node(
    node: "ExecutableNode",
    context: "TypedExecutionContext",
    event_pipeline: "EventPipeline",
    scheduler: "NodeScheduler | None",
    service_registry: Any,
) -> dict[str, Any]:
    """Execute a single node.

    Args:
        node: Node to execute
        context: Execution context
        event_pipeline: Event pipeline for emitting events
        scheduler: Optional scheduler for tracking node state
        service_registry: Service registry for handlers

    Returns:
        Dictionary with execution result
    """
    node_id = node.id
    start_time = time.time()
    epoch = context.current_epoch()

    if scheduler:
        scheduler.mark_node_running(node_id, epoch)

    await event_pipeline.emit("node_started", node=node)

    try:
        if await _should_skip_max_iteration(node, context):
            return await _handle_max_iteration_reached(node, context, event_pipeline)

        output = await _execute_node_handler(node, context, event_pipeline, service_registry)

        from dipeo.diagram_generated import NodeType

        # Always emit tokens for non-condition nodes, even if output is empty/falsy
        # This ensures downstream nodes receive tokens and can become ready
        if node.type != NodeType.CONDITION:
            outputs = {"default": output} if not isinstance(output, dict) else output
            context.emit_outputs_as_tokens(node_id, outputs, epoch)

        duration_ms = (time.time() - start_time) * 1000
        llm_usage = extract_llm_usage(output)

        # Add metadata to envelope if applicable
        if hasattr(output, "meta") and isinstance(output.meta, dict):
            output.meta["execution_time_ms"] = duration_ms
            if llm_usage:
                output.meta["token_usage"] = llm_usage

        await _handle_node_completion(node, output, context, event_pipeline)

        if scheduler:
            scheduler.mark_node_complete(node_id, epoch)

        exec_count = context.state.get_node_execution_count(node.id)
        await event_pipeline.emit(
            "node_completed",
            node=node,
            envelope=output,
            exec_count=exec_count,
            duration_ms=duration_ms,
        )

        return format_node_result(output)

    except Exception as e:
        if scheduler:
            scheduler.mark_node_complete(node_id, epoch)
        await _handle_node_failure(context, node, e, event_pipeline)
        raise


async def _should_skip_max_iteration(
    node: "ExecutableNode", context: "TypedExecutionContext"
) -> bool:
    """Check if node should skip execution due to max iteration."""
    from dipeo.diagram_generated.generated_nodes import PersonJobNode

    if isinstance(node, PersonJobNode):
        current_count = context.state.get_node_execution_count(node.id)
        return current_count >= node.max_iteration
    return False


async def _handle_max_iteration_reached(
    node: "ExecutableNode", context: "TypedExecutionContext", event_pipeline: "EventPipeline"
) -> dict[str, Any]:
    """Handle node that has reached max iteration."""
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

    await event_pipeline.emit("node_completed", node=node, envelope=None, exec_count=current_count)

    return {"value": "", "status": "MAXITER_REACHED"}


async def _execute_node_handler(
    node: "ExecutableNode",
    context: "TypedExecutionContext",
    event_pipeline: "EventPipeline",
    service_registry: Any,
) -> Any:
    """Execute the node's handler."""
    with context.executing_node(node.id):
        context.state.transition_to_running(node.id, context.current_epoch())

        from dipeo.diagram_generated import Status

        handler = get_handler(service_registry, node.type)
        inputs = await handler.resolve_envelope_inputs(
            request=type("TempRequest", (), {"node": node, "context": context})()
        )

        request = _create_execution_request(node, context, inputs, service_registry)
        output = await handler.pre_execute(request)

        if output is None:
            output = await handler.execute_with_envelopes(request, inputs)

        if hasattr(handler, "post_execute"):
            output = handler.post_execute(request, output)

        return output


def _create_execution_request(
    node: "ExecutableNode", context: "TypedExecutionContext", inputs: Any, service_registry: Any
) -> Any:
    """Create execution request for node handler."""
    from dipeo.application.execution.engine.request import ExecutionRequest

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
        services=service_registry,
        metadata=request_metadata,
        execution_id=context.execution_id,
        parent_container=context.container,
        parent_registry=service_registry,
    )


async def _handle_node_failure(
    context: "TypedExecutionContext",
    node: "ExecutableNode",
    error: Exception,
    event_pipeline: "EventPipeline",
) -> None:
    """Handle node execution failure."""
    logger.error(f"Error executing node {node.id}: {error}", exc_info=True)
    context.state.transition_to_failed(node.id, str(error))

    from dipeo.diagram_generated import Status

    await event_pipeline.emit("node_error", node=node, exc=error)


async def _handle_node_completion(
    node: "ExecutableNode",
    envelope: Any,
    context: "TypedExecutionContext",
    event_pipeline: "EventPipeline",
) -> None:
    """Handle successful node completion."""
    context.state.transition_to_completed(node.id, envelope)

    from dipeo.diagram_generated import Status
