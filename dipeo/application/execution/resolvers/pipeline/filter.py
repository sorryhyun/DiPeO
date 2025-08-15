"""Filter stage - filters edges based on execution state and strategy."""

from typing import Any

from dipeo.diagram_generated import NodeType
from dipeo.core.resolution import NodeStrategyFactory
from .base import PipelineStage, PipelineContext


class FilterStage(PipelineStage):
    """Filters edges based on dependency states and node strategies.
    
    This stage:
    1. Gets the node-specific strategy
    2. Checks for special inputs (e.g., PersonJob "first" inputs)
    3. Filters edges based on strategy rules
    4. Handles iteration/branch filtering
    """
    
    def __init__(self):
        self.strategy_factory = NodeStrategyFactory()
    
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Filter edges based on strategy and execution state."""
        
        # Get strategy for this node type
        ctx.node_strategy = self.strategy_factory.get_strategy(ctx.node.type)
        
        # Check for special inputs
        ctx.has_special_inputs = self._has_special_inputs(ctx)
        
        # Filter edges based on strategy
        ctx.filtered_edges = []
        for edge in ctx.incoming_edges:
            if self._should_process_edge(edge, ctx):
                # Also apply iteration/branch filtering
                if self._matches_iteration_branch(edge, ctx):
                    ctx.filtered_edges.append(edge)
        
        return ctx
    
    def _has_special_inputs(self, ctx: PipelineContext) -> bool:
        """Check if node has special inputs like PersonJob 'first' inputs."""
        if ctx.node.type == NodeType.PERSON_JOB and hasattr(ctx.node_strategy, 'has_first_inputs'):
            return ctx.node_strategy.has_first_inputs(ctx.incoming_edges)
        return False
    
    def _should_process_edge(self, edge, ctx: PipelineContext) -> bool:
        """Determine if an edge should be processed based on strategy."""
        return ctx.node_strategy.should_process_edge(
            edge, 
            ctx.node, 
            ctx.context, 
            ctx.has_special_inputs
        )
    
    def _matches_iteration_branch(self, edge, ctx: PipelineContext) -> bool:
        """Check if edge matches current iteration/branch context."""
        
        # Get the edge value from context
        value = ctx.get_edge_value(edge)
        if not value:
            return True  # No value yet, can't filter
        
        # If value is an Envelope with iteration metadata
        from dipeo.core.execution.envelope import Envelope
        if isinstance(value, Envelope):
            # Check iteration match
            if 'iteration' in value.meta:
                current_iteration = self._get_node_iteration(ctx, str(edge.target_node_id))
                if value.meta['iteration'] != current_iteration:
                    return False
            
            # Check branch match
            if 'branch_id' in value.meta:
                active_branch = self._get_active_branch(ctx, str(edge.target_node_id))
                if value.meta['branch_id'] != active_branch:
                    return False
        
        return True
    
    def _get_node_iteration(self, ctx: PipelineContext, node_id: str) -> int:
        """Get current iteration for a node."""
        # Check context for iteration count
        # For now, return 0 as default
        return 0
    
    def _get_active_branch(self, ctx: PipelineContext, node_id: str) -> str | None:
        """Get active branch for a node."""
        # Check if node is in a conditional branch
        # For now, return None
        return None