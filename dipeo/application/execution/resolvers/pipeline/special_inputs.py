"""SpecialInputs stage - handles node-specific input requirements."""

from typing import Any
from uuid import uuid4

from dipeo.diagram_generated import NodeType
from dipeo.core.execution.envelope import EnvelopeFactory
from .base import PipelineStage, PipelineContext


class SpecialInputsStage(PipelineStage):
    """Handles special node-specific inputs.
    
    This stage:
    1. Adds conversation state for PersonJob nodes
    2. Adds system variables
    3. Handles PersonJob "first" execution inputs
    4. Maps inputs to correct variable names
    """
    
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Add special inputs based on node requirements."""
        
        # Handle PersonJob first execution mapping
        if ctx.node.type == NodeType.PERSON_JOB:
            await self._handle_person_job_inputs(ctx)
        
        # Add conversation state if needed
        await self._add_conversation_state(ctx)
        
        # Add system variables
        self._add_system_variables(ctx)
        
        return ctx
    
    async def _handle_person_job_inputs(self, ctx: PipelineContext) -> None:
        """Handle PersonJob specific input mapping."""
        
        for edge in ctx.filtered_edges:
            # Check if this edge is marked for first execution
            if edge.metadata and edge.metadata.get('is_first_execution'):
                # Map the input to the correct template variable name
                # Check if there's a label on the arrow
                if edge.metadata.get('label'):
                    # Use the arrow label as the template variable name
                    input_key = edge.metadata['label']
                else:
                    # No label, use "default" as the template variable name
                    input_key = 'default'
                
                # Store this mapping for later use
                if not hasattr(ctx, 'input_mappings'):
                    ctx.input_mappings = {}
                ctx.input_mappings[edge] = input_key
    
    async def _add_conversation_state(self, ctx: PipelineContext) -> None:
        """Add conversation state for nodes that need it."""
        
        if ctx.node.type == NodeType.PERSON_JOB:
            if hasattr(ctx.node, 'use_conversation_memory') and ctx.node.use_conversation_memory:
                person_id = getattr(ctx.node, 'person', None)
                if person_id:
                    conv_state = await self._get_conversation_state(person_id, ctx.context)
                    if conv_state:
                        trace_id = getattr(ctx.context, 'execution_id', str(uuid4()))
                        ctx.special_inputs['_conversation'] = EnvelopeFactory.conversation(
                            conv_state,
                            produced_by="system",
                            trace_id=trace_id
                        )
    
    def _add_system_variables(self, ctx: PipelineContext) -> None:
        """Add system variables to special inputs."""
        
        if hasattr(ctx.context, 'variables') and ctx.context.variables:
            trace_id = getattr(ctx.context, 'execution_id', str(uuid4()))
            ctx.special_inputs['_variables'] = EnvelopeFactory.json(
                dict(ctx.context.variables),
                produced_by="system",
                trace_id=trace_id
            )
    
    async def _get_conversation_state(self, person_id: str, context) -> dict | None:
        """Get conversation state for a person."""
        # Would fetch from conversation manager
        # For now, return None
        return None