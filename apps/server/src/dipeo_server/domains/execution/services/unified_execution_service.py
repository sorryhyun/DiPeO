"""Unified execution service with ServiceRegistry and direct streaming."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo_core import BaseService, SupportsExecution, get_global_registry
from dipeo_domain import ExecutionStatus, NodeExecutionStatus
from dipeo_domain.models import DomainDiagram, DomainNode, NodeOutput

from dipeo_server.application.execution_context import ExecutionContext
from dipeo_server.domains.execution.services.service_registry import ServiceRegistry
from dipeo_server.infrastructure.persistence import state_store

if TYPE_CHECKING:
    from dipeo_server.application.app_context import AppContext

log = logging.getLogger(__name__)

# Optional: Import streaming manager if available
try:
    from dipeo_server.api.graphql.subscriptions import (
        publish_execution_update,
    )
except ImportError:
    publish_execution_update = None


class UnifiedExecutionService(BaseService, SupportsExecution):
    """Execution service using ServiceRegistry for clean dependency injection."""

    def __init__(self, app_context: AppContext):
        """Initialize with app context."""
        super().__init__()
        self.app_context = app_context
        self.service_registry = ServiceRegistry(app_context)

    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    async def execute_diagram(
        self,
        diagram: dict[str, Any] | str | DomainDiagram,
        options: dict[str, Any],
        execution_id: str,
        interactive_handler: Callable[[dict[str, Any]], Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute diagram with direct streaming via async generator."""
        log.info(
            f"UnifiedExecutionService.execute_diagram called with execution_id: {execution_id}"
        )

        # Prepare diagram
        if self.app_context.execution_preparation_service:
            ready_diagram = await self.app_context.execution_preparation_service.prepare_for_execution(
                diagram=diagram, validate=True
            )
            diagram_obj = ready_diagram.domain_model
            api_keys = ready_diagram.api_keys
        else:
            # Fallback for compatibility
            if isinstance(diagram, dict):
                diagram_obj = DomainDiagram.model_validate(diagram)
            elif isinstance(diagram, str):
                # Load from storage if string ID provided
                diagram_obj = (
                    await self.app_context.diagram_storage_service.load_diagram(diagram)
                )
            else:
                diagram_obj = diagram
            api_keys = {}

        # Import handlers to ensure they are registered
        from dipeo_server.application import handlers  # noqa: F401

        # Create execution in cache
        diagram_id = diagram_obj.metadata.id if diagram_obj.metadata else None
        await state_store.create_execution_in_cache(
            execution_id, diagram_id, options.get("variables", {})
        )

        # Create start update
        start_update = {
            "type": "execution_start",
            "execution_id": execution_id,
        }

        # Yield start
        yield start_update

        # Also publish to streaming manager
        if publish_execution_update:
            await publish_execution_update(execution_id, start_update)

        try:
            # Execute with direct streaming
            final_status = "completed"
            async for update in self._execute_with_streaming(
                diagram_obj, api_keys, execution_id, interactive_handler, options
            ):
                yield update

                # Check for failures
                if update.get("type") == "node_update":
                    state_update = update.get("data", {})
                    if state_update.get("state") == NodeExecutionStatus.FAILED.value:
                        final_status = "failed"

            # Create completion update
            completion_update = {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": final_status,
            }

            # Yield completion
            yield completion_update

            # Also publish to streaming manager
            if publish_execution_update:
                await publish_execution_update(execution_id, completion_update)

        except Exception as e:
            log.error(f"Execution failed for {execution_id}: {e}")
            await state_store.update_status(
                execution_id, ExecutionStatus.FAILED, error=str(e)
            )
            error_completion = {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e),
            }

            yield error_completion

            # Also publish to streaming manager
            if publish_execution_update:
                await publish_execution_update(execution_id, error_completion)
            raise

    async def _execute_with_streaming(
        self,
        diagram: DomainDiagram,
        api_keys: dict[str, str],
        execution_id: str,
        interactive_handler: Callable | None = None,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute diagram nodes with direct streaming."""
        # Create pure data context
        context = ExecutionContext(
            execution_id=execution_id,
            diagram_id=diagram.metadata.id if diagram.metadata else "",
            nodes=diagram.nodes,
            edges=diagram.arrows,
            persons={p.id: p.model_dump() for p in diagram.persons},
            api_keys=api_keys,
            variables=options.get("variables", {}) if options else {},
        )

        # Get handler registry
        handler_registry = get_global_registry()
        log.info(
            f"Registry has {len(handler_registry.list_types())} registered handlers"
        )

        # Build execution graph using ViewBasedEngine
        from dipeo_server.domains.execution.execution_view import ExecutionView

        view = ExecutionView(diagram, handler_registry, api_keys)

        # Execute nodes in order
        completed_nodes = set()
        while True:
            # Find ready nodes
            ready_nodes = []
            for node_id, node_view in view.node_views.items():
                if node_id in completed_nodes:
                    continue

                # Check if all dependencies are complete
                dependencies_complete = all(
                    edge.source_view.id in completed_nodes
                    for edge in node_view.incoming_edges
                )

                if dependencies_complete:
                    ready_nodes.append((node_id, node_view))

            log.info(
                f"Found {len(ready_nodes)} ready nodes: {[n[0] for n in ready_nodes]}"
            )
            log.info(f"Completed nodes: {completed_nodes}")

            if not ready_nodes:
                break  # No more nodes to execute

            # Execute ready nodes
            for node_id, node_view in ready_nodes:
                node = next((n for n in diagram.nodes if n.id == node_id), None)
                if not node:
                    continue

                # Update current node
                context.current_node_id = node_id

                # Create update
                update = {
                    "type": "node_update",
                    "data": {
                        "node_id": node_id,
                        "state": NodeExecutionStatus.RUNNING.value,
                        "execution_id": execution_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_type": node.type,
                    },
                }

                # Yield update
                yield update

                # Also publish to streaming manager if available
                if publish_execution_update:
                    await publish_execution_update(execution_id, update)

                try:
                    # Get handler
                    node_def = handler_registry.get(node.type)
                    if not node_def:
                        raise ValueError(f"No handler found for node type: {node.type}")
                    handler = node_def.handler  # Extract the actual handler function

                    # Get services for this handler type
                    services = self.service_registry.get_handler_services(node.type)

                    # Add special services that some handlers need
                    services["execution_context"] = context
                    services["token_service"] = context  # Context has add_token_usage
                    services["diagram"] = diagram

                    # Add interactive handler if needed
                    if node.type == "user_response" and interactive_handler:
                        services["interactive_handler"] = interactive_handler

                    # Collect inputs
                    inputs = self._collect_inputs(node, context, view)

                    # Execute handler
                    runtime_context = context.to_runtime_context(node_view)
                    output = await handler(
                        context=runtime_context,
                        props=node.data,
                        inputs=inputs,
                        services=services,
                    )

                    # Store output
                    context.node_outputs[node_id] = output
                    context.increment_exec_count(node_id)

                    # Update view
                    node_view.output = output

                    # Create completion update
                    completion_update = {
                        "type": "node_update",
                        "data": {
                            "node_id": node_id,
                            "state": NodeExecutionStatus.COMPLETED.value,
                            "output": output.model_dump()
                            if hasattr(output, "model_dump")
                            else output,
                            "execution_id": execution_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "node_type": node.type,
                        },
                    }

                    # Yield update
                    yield completion_update

                    # Also publish to streaming manager
                    if publish_execution_update:
                        await publish_execution_update(execution_id, completion_update)

                    completed_nodes.add(node_id)

                except Exception as e:
                    log.error(f"Node {node_id} failed: {e}")

                    # Create error output
                    error_output = NodeOutput(
                        value={"error": str(e)},
                        metadata={"status": "failed", "error": str(e)},
                    )
                    context.node_outputs[node_id] = error_output

                    # Create error update
                    error_update = {
                        "type": "node_update",
                        "data": {
                            "node_id": node_id,
                            "state": NodeExecutionStatus.FAILED.value,
                            "error": str(e),
                            "execution_id": execution_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "node_type": node.type,
                        },
                    }

                    # Yield update
                    yield error_update

                    # Also publish to streaming manager
                    if publish_execution_update:
                        await publish_execution_update(execution_id, error_update)

                    completed_nodes.add(node_id)

                    # Continue execution of other branches
                    continue

        # Final state persistence
        await self._persist_final_state(context, execution_id)

    def _collect_inputs(
        self, node: DomainNode, context: ExecutionContext, view: Any
    ) -> dict[str, Any]:
        """Collect inputs for a node from connected outputs."""
        inputs = {}

        # Get incoming edges
        for edge in context.edges:
            if edge.target.split(":")[0] == node.id:
                source_node_id = edge.source.split(":")[0]
                source_output = context.node_outputs.get(source_node_id)

                if source_output:
                    # Use edge label as input key if available
                    input_key = (
                        edge.data.get("label", source_node_id)
                        if edge.data
                        else source_node_id
                    )
                    inputs[input_key] = source_output.value

        return inputs

    async def _persist_final_state(self, context: ExecutionContext, execution_id: str):
        """Persist final execution state."""
        # Aggregate token usage
        total_token_usage = context.get_total_token_usage()

        # Get final state from cache
        final_state = await state_store.get_state_from_cache(execution_id)
        if final_state:
            # Determine final status
            has_failures = any(
                output.metadata and output.metadata.get("status") == "failed"
                for output in context.node_outputs.values()
            )

            final_state.status = (
                ExecutionStatus.FAILED if has_failures else ExecutionStatus.COMPLETED
            )

            if total_token_usage:
                final_state.token_usage = total_token_usage

            # Persist to database
            await state_store.persist_final_state(final_state)

            # Persist conversation history
            if hasattr(
                self.app_context.conversation_service, "persist_execution_conversations"
            ):
                await self.app_context.conversation_service.persist_execution_conversations(
                    execution_id
                )
