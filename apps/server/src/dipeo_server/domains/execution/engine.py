"""Execution engine that directly calls handlers."""

import asyncio
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from dipeo_domain.models import DomainArrow, DomainDiagram, NodeExecutionStatus, NodeOutput

from dipeo_server.core.services import FileService
from dipeo_server.domains.llm.services import LLMService
from dipeo_server.domains.execution.services.state_store import StateStore
from dipeo_server.domains.execution.context import ExecutionContext
from dipeo_server.domains.person.memory import MemoryService
from dipeo_server.domains.integrations.notion import NotionService


class SimplifiedEngine:

    def __init__(self, handlers: Dict[str, Callable]):
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

        await state_store.create_execution(
            ctx.execution_id,
            diagram.id,
            ctx.variables
        )

        execution_order = self._topological_sort(diagram.nodes, diagram.arrows)

        await self._execute_nodes(ctx, execution_order)

        return ctx

    async def _execute_nodes(self, ctx: ExecutionContext, execution_order: List[List[str]]) -> None:

        for level in execution_order:
            tasks = []
            for node_id in level:
                node = self._find_node(ctx.diagram.nodes, node_id)
                if node and self._can_execute(ctx, node_id):
                    tasks.append(self._execute_node(ctx, node))

            if tasks:
                await asyncio.gather(*tasks)

    async def _execute_node(self, ctx: ExecutionContext, node) -> None:
        node_type = node.__class__.__name__
        handler = self.handlers.get(node_type)

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
                    "error": f"No handler found for node type: {node_type}"
                }
            )
            return

        ctx.current_node_id = node.id

        if hasattr(ctx, 'stream_callback') and ctx.stream_callback:
            await ctx.stream_callback({
                "type": "node_start",
                "node_id": node.id,
                "node_type": node_type,
            })

        try:
            output = await handler(node, ctx)
            ctx.set_node_output(node.id, output)

            if hasattr(ctx, 'stream_callback') and ctx.stream_callback:
                await ctx.stream_callback({
                    "type": "node_complete",
                    "node_id": node.id,
                    "status": output.status,
                    "output": output,
                    "outputs": output.outputs,
                    "error": output.error,
                    "metadata": output.metadata,
                })
        except Exception as e:
            await ctx.state_store.update_node_status(
                ctx.execution_id, node.id, NodeExecutionStatus.FAILED
            )
            error_output = NodeOutput(
                value={},
                metadata={
                    "node_id": node.id,
                    "exec_id": f"{node.id}_{ctx.exec_counts.get(node.id, 0) + 1}",
                    "status": "failed",
                    "error": str(e)
                }
            )
            ctx.set_node_output(node.id, error_output)

            if hasattr(ctx, 'stream_callback') and ctx.stream_callback:
                await ctx.stream_callback({
                    "type": "node_complete",
                    "node_id": node.id,
                    "status": "failed",
                    "output": error_output,
                    "outputs": {},
                    "error": str(e),
                    "metadata": {},
                })

    def _can_execute(self, ctx: ExecutionContext, node_id: str) -> bool:
        incoming_edges = ctx.find_edges_to(node_id)

        for edge in incoming_edges:
            source_output = ctx.get_node_output(edge.from_node)
            if not source_output or source_output.status != "completed":
                return False

        return True

    def _topological_sort(self, nodes, arrows: List[DomainArrow]) -> List[List[str]]:
        adj_list = {node.id: [] for node in nodes}
        in_degree = {node.id: 0 for node in nodes}

        for arrow in arrows:
            if arrow.from_node in adj_list:
                adj_list[arrow.from_node].append(arrow.to_node)
                if arrow.to_node in in_degree:
                    in_degree[arrow.to_node] += 1

        levels = []
        current_level = [node_id for node_id, degree in in_degree.items() if degree == 0]

        while current_level:
            levels.append(current_level[:])
            next_level = []

            for node_id in current_level:
                for neighbor in adj_list[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)

            current_level = next_level

        return levels

    def _find_node(self, nodes, node_id: str):
        for node in nodes:
            if node.id == node_id:
                return node
        return None
