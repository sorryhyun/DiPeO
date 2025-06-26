"""Execution engine using ExecutionView for efficiency."""

import asyncio
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from dipeo_domain.models import DomainDiagram, NodeExecutionStatus, NodeOutput

from dipeo_server.domains.llm.services import LLMService
from dipeo_server.infrastructure.persistence import FileService

from ..integrations.notion import NotionService
from ..person.memory import MemoryService
from .context import ExecutionContext
from .execution_view import ExecutionView, NodeView


class ViewBasedEngine:
    def __init__(self, handlers: Dict[str, Callable]) -> None:
        self.handlers = handlers

    async def execute_diagram(
        self,
        diagram: DomainDiagram,
        api_keys: Dict[str, str],
        llm_service: LLMService,
        file_service: FileService,
        memory_service: MemoryService,
        notion_service: NotionService,
        state_store: Optional[Any] = None,
        execution_id: Optional[str] = None,
        interactive_handler: Optional[Callable] = None,
        stream_callback: Optional[Callable] = None,
    ) -> ExecutionContext:
        view = ExecutionView(diagram, self.handlers, api_keys)

        ctx = ExecutionContext(
            diagram=diagram,
            edges=diagram.arrows,
            execution_id=execution_id or str(uuid4()),
            api_keys=api_keys,
            llm_service=llm_service,
            file_service=file_service,
            memory_service=memory_service,
            notion_service=notion_service,
            state_store=state_store,
        )

        if interactive_handler:
            ctx.interactive_handler = interactive_handler

        if stream_callback:
            ctx.stream_callback = stream_callback

        ctx._execution_view = view

        if state_store:
            import logging

            log = logging.getLogger(__name__)

            state = await state_store.get_state(ctx.execution_id)
            if state and state.node_outputs:
                for node_id, output in state.node_outputs.items():
                    ctx.set_node_output(node_id, output)
            else:
                log.info("No existing node outputs found in state store")

        await self._execute_with_view(ctx, view)

        return ctx

    async def _execute_with_view(
        self, ctx: ExecutionContext, view: ExecutionView
    ) -> None:
        import logging

        log = logging.getLogger(__name__)

        for level_num, level_nodes in enumerate(view.execution_order):
            tasks = []
            for node_view in level_nodes:
                if self._can_execute_node_view(node_view):
                    tasks.append(self._execute_node_view(ctx, node_view))
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
                    current_exec_count = ctx.exec_counts.get(node_id, 0)
                    
                    if current_exec_count >= max_iter:
                        continue
                if self._can_execute_node_view(node_view):
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

            tasks = []
            for node_view in ready_nodes:
                tasks.append(self._execute_node_view(ctx, node_view))

            await asyncio.gather(*tasks)
            
            # After executing nodes, check if any condition nodes triggered a loop
            for node_view in ready_nodes:
                if node_view.node.type == "condition" and node_view.output:
                    condition_result = node_view.output.metadata.get("condition_result", False)
                    if not condition_result:  # False means loop should continue
                        # Find all nodes that should re-execute in the loop
                        self._clear_loop_node_outputs(node_view, view, ctx)

        log.info("All execution completed")

    def _can_execute_node_view(self, node_view: NodeView) -> bool:
        import logging
        log = logging.getLogger(__name__)
        
        # If node already has output, it's already been executed
        if node_view.output is not None:
            return False
            
        if node_view.node.type == "person_job":
            first_edges = [
                e for e in node_view.incoming_edges if e.target_handle == "first"
            ]
            if first_edges and any(
                edge.source_view.output is not None for edge in first_edges
            ):
                return True
        for edge in node_view.incoming_edges:
            if edge.source_view.node.type == "condition":
                log.debug(
                    f"Checking condition edge from {edge.source_view.id} to {node_view.id}, "
                    f"output exists: {edge.source_view.output is not None}"
                )
                if edge.source_view.output is not None:
                    condition_result = edge.source_view.output.metadata.get("condition_result", False)
                    edge_branch = edge.arrow.data.get("branch", None) if edge.arrow.data else None
                    
                    log.debug(
                        f"Condition result: {condition_result}, edge branch: {edge_branch}, "
                        f"edge data: {edge.arrow.data}"
                    )
                    
                    if edge_branch is not None:
                        edge_branch_bool = edge_branch.lower() == "true"
                        
                        if edge_branch_bool != condition_result:
                            log.debug(
                                f"Skipping edge from {edge.source_view.id} to {node_view.id} - "
                                f"branch {edge_branch} doesn't match condition result {condition_result}"
                            )
                            # This edge doesn't match the condition, skip to next edge
                            continue
                        
                        # This edge matches the condition, check if output exists
                        if edge.source_view.output is None:
                            return False
                    else:
                        # No branch specified, require output to exist
                        if edge.source_view.output is None:
                            return False
                else:
                    # Condition node has no output yet
                    return False
            else:
                # Non-condition node
                if edge.source_view.output is None:
                    log.debug(
                        f"Node {node_view.id} waiting for output from {edge.source_view.id}"
                    )
                    return False
        
        log.debug(f"Node {node_view.id} is ready to execute")
        return True
    
    def _clear_loop_node_outputs(
        self, condition_view: NodeView, view: ExecutionView, ctx: ExecutionContext
    ) -> None:
        """Clear outputs of nodes that should re-execute when a condition triggers a loop."""
        import logging
        log = logging.getLogger(__name__)
        
        # Find edges from the condition node with false branch
        false_edges = [
            edge for edge in condition_view.outgoing_edges
            if edge.arrow.data and edge.arrow.data.get("branch", "").lower() == "false"
        ]
        
        # Only clear direct targets of false branches for now
        for edge in false_edges:
            target_view = edge.target_view
            if target_view and target_view.output is not None:
                # Check if this node hasn't reached its max iterations yet
                max_iter = 1
                if target_view.node.type in ["job", "person_job"] and target_view.node.data:
                    max_iter = target_view.node.data.get("maxIteration", 1)
                
                current_exec_count = ctx.exec_counts.get(target_view.id, 0)
                if current_exec_count < max_iter:
                    log.debug(
                        f"Clearing output for node {target_view.id} to allow re-execution in loop "
                        f"(exec_count: {current_exec_count}, max_iter: {max_iter})"
                    )
                    target_view.output = None
                    # Also clear from context
                    if target_view.id in ctx.node_outputs:
                        del ctx.node_outputs[target_view.id]

    async def _execute_node_view(
        self, ctx: ExecutionContext, node_view: NodeView
    ) -> None:
        node = node_view.node
        handler = node_view.handler

        if not handler:
            await ctx.state_store.update_node_status(
                ctx.execution_id, node.id, NodeExecutionStatus.FAILED
            )
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

        ctx.current_node_id = node.id
        node_view.exec_count += 1
        ctx.exec_counts[node.id] = node_view.exec_count

        await ctx.state_store.update_node_status(
            ctx.execution_id, node.id, NodeExecutionStatus.RUNNING
        )

        if ctx.stream_callback:
            await ctx.stream_callback(
                {
                    "type": "node_start",
                    "node_id": node.id,
                    "node_type": node.type,
                }
            )

        try:
            output = await self._call_handler_with_view(handler, node, node_view, ctx)

            node_view.output = output
            ctx.set_node_output(node.id, output)

            await ctx.state_store.update_node_status(
                ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED
            )

            if ctx.stream_callback:
                metadata = output.metadata or {}
                status = metadata.get("status", "completed")
                outputs = output.value if isinstance(output.value, dict) else {}
                error = metadata.get("error", None)

                await ctx.stream_callback(
                    {
                        "type": "node_complete",
                        "node_id": node.id,
                        "status": status,
                        "output": output.model_dump(),
                        "outputs": outputs,
                        "error": error,
                        "metadata": metadata,
                    }
                )
        except Exception as e:
            await ctx.state_store.update_node_status(
                ctx.execution_id, node.id, NodeExecutionStatus.FAILED
            )
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
            ctx.set_node_output(node.id, error_output)

            if ctx.stream_callback:
                await ctx.stream_callback(
                    {
                        "type": "node_complete",
                        "node_id": node.id,
                        "status": "failed",
                        "output": error_output.model_dump(),
                        "outputs": {},
                        "error": str(e),
                        "metadata": error_output.metadata or {},
                    }
                )

    async def _call_handler_with_view(
        self, handler: Callable, node, node_view: NodeView, ctx: ExecutionContext
    ) -> NodeOutput:
        import inspect

        sig = inspect.signature(handler)

        if "node_view" in sig.parameters:
            return await handler(node=node, node_view=node_view, ctx=ctx)
        return await handler(node, ctx)
