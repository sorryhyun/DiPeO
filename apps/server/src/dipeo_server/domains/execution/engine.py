"""Execution engine using ExecutionView for efficiency while keeping DomainDiagram."""

import asyncio
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from dipeo_domain.models import DomainDiagram, NodeExecutionStatus, NodeOutput

from .execution_view import ExecutionView, NodeView
from .context import ExecutionContext
from ..person.memory import MemoryService
from ..integrations.notion import NotionService
from dipeo_server.core.services import FileService
from dipeo_server.domains.llm.services import LLMService
from .services.state_store import StateStore


class ViewBasedEngine:
    """Engine that uses ExecutionView for efficient access to DomainDiagram."""
    
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
        """Execute diagram using efficient view."""
        
        # Create execution view for efficient access
        view = ExecutionView(diagram, self.handlers, api_keys)
        
        # Create context (still uses original diagram for compatibility)
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
        
        # Store view in context for handler access
        ctx._execution_view = view
        
        await state_store.create_execution(
            ctx.execution_id,
            diagram.id if hasattr(diagram, 'id') else None,
            ctx.variables
        )
        
        # Execute using view's pre-computed order
        await self._execute_with_view(ctx, view)
        
        return ctx
    
    async def _execute_with_view(self, ctx: ExecutionContext, view: ExecutionView) -> None:
        """Execute nodes using the efficient view."""
        
        for level_num, level_nodes in enumerate(view.execution_order):
            # Execute all nodes in level concurrently
            tasks = []
            for node_view in level_nodes:
                if self._can_execute_node_view(node_view):
                    tasks.append(self._execute_node_view(ctx, node_view))
            
            if tasks:
                await asyncio.gather(*tasks)
    
    def _can_execute_node_view(self, node_view: NodeView) -> bool:
        """Check if node is ready using view."""
        # All incoming nodes must have output
        return all(edge.source_view.output is not None 
                   for edge in node_view.incoming_edges)
    
    async def _execute_node_view(self, ctx: ExecutionContext, node_view: NodeView) -> None:
        """Execute a single node using view."""
        node = node_view.node  # Original node
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
                    "error": f"No handler found for node type: {node.type}"
                }
            )
            node_view.output = error_output
            return
        
        # Update context
        ctx.current_node_id = node.id
        node_view.exec_count += 1
        ctx.exec_counts[node.id] = node_view.exec_count
        
        if ctx.stream_callback:
            await ctx.stream_callback({
                "type": "node_start",
                "node_id": node.id,
                "node_type": node.type,
            })
        
        try:
            # Call handler with view-aware wrapper
            output = await self._call_handler_with_view(handler, node, node_view, ctx)
            
            # Store output in both places
            node_view.output = output
            ctx.set_node_output(node.id, output)
            
            if ctx.stream_callback:
                # Extract status, outputs, and error from metadata/value
                metadata = output.metadata or {}
                status = metadata.get("status", "completed")
                outputs = output.value if isinstance(output.value, dict) else {}
                error = metadata.get("error", None)
                
                await ctx.stream_callback({
                    "type": "node_complete",
                    "node_id": node.id,
                    "status": status,
                    "output": output.model_dump(),
                    "outputs": outputs,
                    "error": error,
                    "metadata": metadata,
                })
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
                    "error": str(e)
                }
            )
            node_view.output = error_output
            ctx.set_node_output(node.id, error_output)
            
            if ctx.stream_callback:
                await ctx.stream_callback({
                    "type": "node_complete",
                    "node_id": node.id,
                    "status": "failed",
                    "output": error_output.model_dump(),
                    "outputs": {},
                    "error": str(e),
                    "metadata": error_output.metadata or {},
                })
    
    async def _call_handler_with_view(
        self, 
        handler: Callable, 
        node,  # DomainNode type 
        node_view: NodeView,
        ctx: ExecutionContext
    ) -> NodeOutput:
        """Call handler, injecting view if it supports it."""
        # Check if handler accepts node_view parameter
        import inspect
        sig = inspect.signature(handler)
        
        if 'node_view' in sig.parameters:
            # New view-aware handler
            return await handler(node=node, node_view=node_view, ctx=ctx)
        else:
            # Legacy handler
            return await handler(node, ctx)

