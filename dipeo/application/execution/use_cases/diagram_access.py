"""Lightweight helper for context-aware diagram operations."""
from typing import Any
from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.diagram_generated.domain_models import NodeID, Status


class DiagramAccess:
    """Lightweight helper for context-aware diagram operations."""
    
    def get_node_with_state(self, ctx: ExecutionContext, node_id: NodeID) -> tuple[ExecutableNode | None, Any]:
        """Get node and its current execution state."""
        node = ctx.diagram.get_node(node_id) if ctx.diagram else None
        state = ctx.get_node_state(node_id) if hasattr(ctx, "get_node_state") else None
        return node, state
    
    def should_skip_node(self, ctx: ExecutionContext, node_id: NodeID) -> bool:
        """Check if node should be skipped based on execution state."""
        if hasattr(ctx, "get_node_state"):
            state = ctx.get_node_state(node_id)
            return bool(state and state.status in (Status.COMPLETED, Status.SKIPPED))
        return False
    
    def get_branch_targets(self, ctx: ExecutionContext, condition_node_id: NodeID, branch: str) -> list[ExecutableNode]:
        """Get target nodes for a specific condition branch."""
        if not ctx.diagram:
            return []
        
        edges = ctx.diagram.get_outgoing_edges(condition_node_id)
        targets = []
        for edge in edges:
            if edge.source_output == branch:
                node = ctx.diagram.get_node(edge.target_node_id)
                if node:
                    targets.append(node)
        return targets
    
    def get_ready_dependencies(self, ctx: ExecutionContext, node_id: NodeID) -> dict[str, Any]:
        """Get outputs from completed dependencies."""
        if not ctx.diagram:
            return {}
        
        ready = {}
        for edge in ctx.diagram.get_incoming_edges(node_id):
            if not self.should_skip_node(ctx, edge.source_node_id):
                if hasattr(ctx, "get_node_output"):
                    output = ctx.get_node_output(edge.source_node_id)
                    if output:
                        ready[edge.source_output or "default"] = output
        return ready