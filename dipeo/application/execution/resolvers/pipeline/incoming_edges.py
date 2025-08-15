"""IncomingEdges stage - collects edges targeting a node."""

from typing import Any

from dipeo.core.execution.envelope import Envelope
from dipeo.core.resolution import StandardNodeOutput
from .base import PipelineStage, PipelineContext


class IncomingEdgesStage(PipelineStage):
    """Collects all edges targeting the node and retrieves their values.
    
    This stage:
    1. Finds all edges targeting the current node
    2. Retrieves the output value from each source node
    3. Converts outputs to a standard format
    """
    
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Collect incoming edges and their values."""
        
        # Find all edges targeting this node
        ctx.incoming_edges = [
            edge for edge in ctx.diagram.edges
            if edge.target_node_id == ctx.node.id
        ]
        
        # Retrieve values from source nodes
        for edge in ctx.incoming_edges:
            value = self._get_edge_value(edge, ctx)
            if value is not None:
                ctx.set_edge_value(edge, value)
        
        return ctx
    
    def _get_edge_value(self, edge, ctx: PipelineContext) -> Any:
        """Extract value from edge's source node output.
        
        SEAC: Strict extraction based on content_type only, no structural edits.
        """
        source_output = ctx.context.get_node_output(edge.source_node_id)
        
        if not source_output:
            return None
        
        # Handle pure Envelope instances - strict extraction
        if isinstance(source_output, Envelope):
            # Extract based on content_type only
            if source_output.content_type == "raw_text":
                # Text content - return as string
                return StandardNodeOutput.from_value(str(source_output.body))
            elif source_output.content_type == "object":
                # Object content - return as-is (dict, list, or pydantic model)
                return StandardNodeOutput.from_value(source_output.body)
            elif source_output.content_type == "conversation_state":
                # Conversation state - return structured payload
                return StandardNodeOutput.from_value(source_output.body)
            elif source_output.content_type == "condition_result":
                # Special handling for condition outputs (backward compatibility)
                branch_taken = source_output.meta.get("branch_taken")
                branch_data = source_output.meta.get("branch_data", {})
                if branch_taken == "true":
                    output_value = {"condtrue": branch_data}
                else:
                    output_value = {"condfalse": branch_data}
                return StandardNodeOutput.from_dict(output_value)
            else:
                # Unknown content type - return body as-is
                return StandardNodeOutput.from_value(source_output.body)
        
        # Handle dict format or raw value as fallback (backward compatibility)
        if isinstance(source_output, dict) and "value" in source_output:
            return StandardNodeOutput.from_value(source_output["value"])
        else:
            return StandardNodeOutput.from_value(source_output)