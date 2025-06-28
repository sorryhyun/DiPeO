"""Execution engine using ExecutionView for efficiency."""

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from dipeo_core import HandlerRegistry
from dipeo_domain.models import DomainDiagram, NodeOutput

from dipeo_server.application.execution_context import ExecutionContext
from dipeo_server.infrastructure.external.integrations.notion import NotionService
from dipeo_server.infrastructure.external.llm.services import LLMService
from dipeo_server.infrastructure.persistence import FileService

from ..conversation import ConversationService
from .execution_view import EdgeView, ExecutionView, NodeView


class ViewBasedEngine:
    def __init__(self, handler_registry: HandlerRegistry) -> None:
        self.handler_registry = handler_registry

    async def execute_diagram(
        self,
        diagram: DomainDiagram,
        api_keys: dict[str, str],
        llm_service: LLMService,
        file_service: FileService,
        conversation_service: ConversationService,
        notion_service: NotionService = None,
        api_key_service: Any | None = None,
        state_store: Any | None = None,
        execution_id: str | None = None,
        interactive_handler: Callable | None = None,
        stream_callback: Callable | None = None,
    ) -> ExecutionContext:
        view = ExecutionView(diagram, self.handler_registry, api_keys)

        context = ExecutionContext(
            diagram=diagram,
            edges=diagram.arrows,
            execution_id=execution_id or str(uuid4()),
            api_keys=api_keys,
            llm_service=llm_service,
            file_service=file_service,
            conversation_service=conversation_service,
            notion_service=notion_service,
            api_key_service=api_key_service,
            state_store=state_store,
        )

        if interactive_handler:
            context.interactive_handler = interactive_handler

        if stream_callback:
            context.stream_callback = stream_callback

        context._execution_view = view

        if state_store:
            import logging

            log = logging.getLogger(__name__)

            state = await state_store.get_state(context.execution_id)
            if state and state.node_outputs:
                for node_id, output in state.node_outputs.items():
                    context.set_node_output(node_id, output)
            else:
                log.info("No existing node outputs found in state store")

        await self._execute_with_view(context, view)

        return context

    async def _execute_with_view(
        self, context: ExecutionContext, view: ExecutionView
    ) -> None:
        import logging

        log = logging.getLogger(__name__)

        for level_num, level_nodes in enumerate(view.execution_order):
            tasks = []
            for node_view in level_nodes:
                if self._can_execute_node_view(node_view, context):
                    tasks.append(self._execute_node_view(context, node_view))
                else:
                    log.warning(
                        f"Cannot execute node {node_view.node.id} - dependencies not met"
                    )

            if tasks:
                await asyncio.gather(*tasks)
            else:
                log.warning(f"No tasks to execute for level {level_num}")

        max_iterations = 100
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            ready_nodes = []

            for node_id, node_view in view.node_views.items():
                if node_view.node.type in ["job", "person_job"]:
                    max_iter = (
                        node_view.node.data.get("maxIteration", 1)
                        if node_view.node.data
                        else 1
                    )
                    current_exec_count = context.exec_counts.get(node_id, 0)

                    if current_exec_count >= max_iter:
                        continue
                if self._can_execute_node_view(node_view, context):
                    log.debug(f"Node {node_id} is ready to execute")
                    ready_nodes.append(node_view)
                else:
                    incoming_status = []
                    for edge in node_view.incoming_edges:
                        has_output = edge.source_view.output is not None
                        incoming_status.append(f"{edge.source_view.id}:{has_output}")
                    log.debug(
                        f"Node {node_id} is not ready. Incoming edges: {incoming_status}"
                    )

            if not ready_nodes:
                break

            # Add metadata for nodes that have exceeded maxIteration
            for node_id, node_view in view.node_views.items():
                if (
                    node_view.node.type in ["job", "person_job"]
                    and context.exec_counts.get(node_id, 0)
                    >= node_view.node.data.get("maxIteration", 1)
                    and node_view.output
                    and not node_view.output.metadata.get("skipped_due_to_max_iter")
                ):
                    node_view.output.metadata["skipped_due_to_max_iter"] = True

            tasks = []
            for node_view in ready_nodes:
                tasks.append(self._execute_node_view(context, node_view))

            await asyncio.gather(*tasks)

            # After executing nodes, check if any condition nodes triggered a loop
            for node_view in ready_nodes:
                if node_view.node.type == "condition" and node_view.output:
                    condition_result = node_view.output.metadata.get(
                        "condition_result", False
                    )
                    if not condition_result:  # False means loop should continue
                        # Find all nodes that should re-execute in the loop
                        self._clear_loop_node_outputs(node_view, view, context)

        log.info("All execution completed")

    def _get_required_edges(
        self, node_view: NodeView, context: ExecutionContext
    ) -> list[EdgeView]:
        if node_view.node.type == "person_job":
            exec_count = context.exec_counts.get(node_view.id, 0)

            first_edges = [
                e for e in node_view.incoming_edges if e.target_handle == "first"
            ]
            default_edges = [
                e for e in node_view.incoming_edges if e.target_handle == "default"
            ]

            # ── first execution ─────────────────────────────────────────────
            if exec_count == 0:
                return [e for e in first_edges if e.source_view.output is not None] or [
                    e for e in default_edges if e.source_view.output is not None
                ]

            # ── 2nd execution and later ────────────────────────────────────
            ready_defaults = [
                e for e in default_edges if e.source_view.output is not None
            ]

            # If none of the default edges has data yet we *must* wait, so
            # keep the full list → the node will stay “not ready”.
            return ready_defaults or default_edges

        # all other node types
        return node_view.incoming_edges

    def _can_execute_node_view(
        self, node_view: NodeView, context: ExecutionContext
    ) -> bool:
        import logging

        log = logging.getLogger(__name__)

        # If node already has output, it's already been executed
        if node_view.output is not None:
            return False

        required_edges = self._get_required_edges(node_view, context)

        # If no required edges (e.g., start node), it can execute
        if not required_edges:
            log.debug(f"Node {node_view.id} has no required edges, can execute")
            return True

        matched_edge_found = False

        # Check if all required edges are satisfied
        for edge in required_edges:
            if edge.source_view.node.type == "condition":
                if edge.source_view.output is None:
                    return False

                condition_result = edge.source_view.output.metadata.get(
                    "condition_result", False
                )
                edge_branch = (
                    edge.arrow.data.get("branch", None) if edge.arrow.data else None
                )

                if edge_branch is not None:
                    if (edge_branch.lower() == "true") != condition_result:
                        # Mismatched branch ⇒ ignore this edge
                        continue
                # If we get here the branch matches and output exists
                matched_edge_found = True

            else:
                if edge.source_view.output is None:
                    return False
                matched_edge_found = True

        return matched_edge_found

    def _clear_loop_node_outputs(
        self, condition_view: NodeView, view: ExecutionView, context: ExecutionContext
    ) -> None:
        """Clear outputs of nodes that should re-execute when a condition triggers a loop."""
        import logging

        log = logging.getLogger(__name__)

        # Find edges from the condition node with false branch
        false_edges = [
            edge
            for edge in condition_view.outgoing_edges
            if edge.arrow.data and edge.arrow.data.get("branch", "").lower() == "false"
        ]

        # Only clear direct targets of false branches for now
        for edge in false_edges:
            target_view = edge.target_view
            if target_view and target_view.output is not None:
                # Check if this node hasn't reached its max iterations yet
                max_iter = 1
                if (
                    target_view.node.type in ["job", "person_job"]
                    and target_view.node.data
                ):
                    max_iter = target_view.node.data.get("maxIteration", 1)

                current_exec_count = context.exec_counts.get(target_view.id, 0)
                if current_exec_count < max_iter:
                    log.debug(
                        f"Clearing output for node {target_view.id} to allow re-execution in loop "
                        f"(exec_count: {current_exec_count}, max_iter: {max_iter})"
                    )
                    target_view.output = None
                    # Also clear from context
                    if target_view.id in context.node_outputs:
                        del context.node_outputs[target_view.id]

    async def _execute_node_view(
        self, context: ExecutionContext, node_view: NodeView
    ) -> None:
        node = node_view.node
        handler = node_view.handler

        if not handler:
            # Node-level persistence removed - only persist at diagram level
            # await context.state_store.update_node_status(
            #     context.execution_id, node.id, NodeExecutionStatus.FAILED
            # )
            error_output = NodeOutput(
                value={},
                metadata={
                    "node_id": node.id,
                    "exec_id": f"{node.id}_1",
                    "status": "failed",
                    "error": f"No handler found for node type: {node.type}",
                },
            )
            node_view.output = error_output
            return

        context.current_node_id = node.id
        node_view.exec_count += 1
        context.exec_counts[node.id] = node_view.exec_count

        # Node-level persistence removed - only persist at diagram level
        # await context.state_store.update_node_status(
        #     context.execution_id, node.id, NodeExecutionStatus.RUNNING
        # )

        if context.stream_callback:
            await context.stream_callback(
                {
                    "type": "node_start",
                    "node_id": node.id,
                    "node_type": node.type,
                }
            )

        try:
            output = await self._call_handler_with_view(
                handler, node, node_view, context
            )

            node_view.output = output
            context.set_node_output(node.id, output)

            # Node-level persistence removed - only persist at diagram level
            # await context.state_store.update_node_status(
            #     context.execution_id, node.id, NodeExecutionStatus.COMPLETED
            # )

            if context.stream_callback:
                metadata = output.metadata or {}
                status = metadata.get("status", "completed")
                outputs = output.value if isinstance(output.value, dict) else {}
                error = metadata.get("error", None)

                # Build state snapshot for real-time updates
                from dipeo_domain import NodeExecutionStatus

                node_states = {}
                if hasattr(context, "_execution_view") and context._execution_view:
                    for nid, nview in context._execution_view.node_views.items():
                        if nview.output is not None:
                            node_states[nid] = {
                                "status": NodeExecutionStatus.COMPLETED.value,
                                "started_at": None,  # Would need to track this
                                "ended_at": None,  # Would need to track this
                            }

                state_snapshot = {
                    "execution_id": context.execution_id,
                    "status": "running",  # Execution is still running
                    "node_states": node_states,
                    "token_usage": context.get_total_token_usage().model_dump()
                    if hasattr(context, "get_total_token_usage")
                    else None,
                }

                await context.stream_callback(
                    {
                        "type": "node_complete",
                        "node_id": node.id,
                        "status": status,
                        "output": output.model_dump(),
                        "outputs": outputs,
                        "error": error,
                        "metadata": metadata,
                        "state_snapshot": state_snapshot,
                    }
                )
        except Exception as e:
            # Node-level persistence removed - only persist at diagram level
            # await context.state_store.update_node_status(
            #     context.execution_id, node.id, NodeExecutionStatus.FAILED
            # )
            error_output = NodeOutput(
                value={},
                metadata={
                    "node_id": node.id,
                    "exec_id": f"{node.id}_{node_view.exec_count}",
                    "status": "failed",
                    "error": str(e),
                },
            )
            node_view.output = error_output
            context.set_node_output(node.id, error_output)

            if context.stream_callback:
                # Build state snapshot for real-time updates
                from dipeo_domain import NodeExecutionStatus

                node_states = {}
                if hasattr(context, "_execution_view") and context._execution_view:
                    for nid, nview in context._execution_view.node_views.items():
                        if nview.output is not None:
                            node_states[nid] = {
                                "status": NodeExecutionStatus.COMPLETED.value,
                                "started_at": None,
                                "ended_at": None,
                            }

                # Current node failed
                node_states[node.id] = {
                    "status": NodeExecutionStatus.FAILED.value,
                    "started_at": None,
                    "ended_at": None,
                    "error": str(e),
                }

                state_snapshot = {
                    "execution_id": context.execution_id,
                    "status": "running",  # Execution might still continue
                    "node_states": node_states,
                    "token_usage": context.get_total_token_usage().model_dump()
                    if hasattr(context, "get_total_token_usage")
                    else None,
                }

                await context.stream_callback(
                    {
                        "type": "node_complete",
                        "node_id": node.id,
                        "status": "failed",
                        "output": error_output.model_dump(),
                        "outputs": {},
                        "error": str(e),
                        "metadata": error_output.metadata or {},
                        "state_snapshot": state_snapshot,
                    }
                )

    async def _call_handler_with_view(
        self, handler: Callable, node, node_view: NodeView, context: ExecutionContext
    ) -> NodeOutput:
        # All handlers now use the new BaseNodeHandler interface
        # which expects props, context, inputs, and services

        # Get node definition from registry
        node_def = self.handler_registry.get(node.type)
        if not node_def:
            raise ValueError(f"No handler found for node type: {node.type}")

        # Update current node ID
        context.current_node_id = node.id

        # Convert contexts
        runtime_context = context.to_runtime_context(node_view)

        # Validate and parse node data
        node_data = node.data or {}
        props = node_def.node_schema(**node_data)

        # Collect inputs from node_view
        inputs = {}
        if node_view:
            inputs = node_view.get_active_inputs()

        # Create services
        services = context.get_services_dict()

        # Execute handler
        return await handler(
            props=props,
            context=runtime_context,
            inputs=inputs,
            services=services,
        )
