"""Execution engine using ExecutionView for efficiency."""

import asyncio
from typing import Callable, Dict, Optional
from uuid import uuid4

from dipeo_domain.models import DomainDiagram, NodeExecutionStatus, NodeOutput

from dipeo_server.domains.llm.services import LLMService
from dipeo_server.infrastructure.persistence import FileService

from ..integrations.notion import NotionService
from ..person.memory import MemoryService
from .context import ExecutionContext
from .execution_view import ExecutionView, NodeView
from .services.state_store import StateStore


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
        state_store: StateStore = None,
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

        # Load existing node outputs from state store if available
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

        # First execute the pre-computed levels
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

        # After initial levels, check for any nodes that became ready due to cycles

        # Continue executing nodes that become ready
        max_iterations = 100  # Prevent infinite loops
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            ready_nodes = []

            for node_id, node_view in view.node_views.items():
                # Check if node has reached max iterations
                max_iter = (
                    node_view.node.data.get("maxIteration", 1)
                    if node_view.node.data
                    else 1
                )
                current_exec_count = ctx.exec_counts.get(node_id, 0)

                if current_exec_count < max_iter:
                    if self._can_execute_node_view(node_view):
                        ready_nodes.append(node_view)

            if not ready_nodes:
                break

            tasks = []
            for node_view in ready_nodes:
                tasks.append(self._execute_node_view(ctx, node_view))

            await asyncio.gather(*tasks)

        log.info("All execution completed")

    def _can_execute_node_view(self, node_view: NodeView) -> bool:
        # For person_job nodes, check if they have input on their "first" handle
        # This allows them to start even if other inputs aren't ready yet
        if node_view.node.type == "person_job":
            # Check if any edge to "first" handle has output
            first_edges = [
                e for e in node_view.incoming_edges if e.target_handle == "first"
            ]
            if first_edges and any(
                edge.source_view.output is not None for edge in first_edges
            ):
                return True

        # For all other nodes (and person_job without first input), require all inputs
        return all(
            edge.source_view.output is not None for edge in node_view.incoming_edges
        )

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

        # Update node status to RUNNING in state store
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

            # Update node status to COMPLETED in state store
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
