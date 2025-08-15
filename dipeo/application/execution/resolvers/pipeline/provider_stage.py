"""Provider stage - handles explicit provider-based inputs.

This replaces the implicit special_inputs stage with an explicit,
opt-in provider system based on node specifications.
"""

from typing import Any
from uuid import uuid4

from dipeo.diagram_generated import NodeType
from dipeo.core.execution.envelope import get_envelope_factory
from .base import PipelineStage, PipelineContext
from .providers import get_provider
from ...node_specs import get_node_spec


class ProviderStage(PipelineStage):
    """Handles provider-based inputs for nodes.
    
    This stage:
    1. Looks up the node's specification
    2. Identifies inputs that come from providers
    3. Invokes the appropriate providers
    4. Adds provider outputs to the inputs
    
    Unlike the old SpecialInputsStage, this is:
    - Explicit: nodes must declare provider inputs in their spec
    - Typed: providers have explicit content types
    - Opt-in: no magic injection of undeclared inputs
    """
    
    name = "ProviderStage"
    
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Apply providers based on node specification."""
        
        # Get the node's specification
        node_spec = get_node_spec(ctx.node.type.value)
        if not node_spec:
            # No spec = no provider inputs
            return ctx
        
        # Get provider inputs from the spec
        provider_inputs = node_spec.get_provider_inputs()
        if not provider_inputs:
            # No provider inputs declared
            return ctx
        
        # Invoke each provider
        for input_name, provider_name in provider_inputs.items():
            provider = get_provider(provider_name)
            if not provider:
                # Provider not found - this is an error in the spec
                if hasattr(ctx, 'validation_errors'):
                    ctx.validation_errors.append(
                        f"Provider '{provider_name}' not found for input '{input_name}'"
                    )
                continue
            
            # Invoke the provider
            envelope = await provider.provide(ctx.context)
            if envelope:
                # Add to special inputs (these don't come from edges)
                ctx.special_inputs[input_name] = envelope
        
        # Handle PersonJob first execution mapping separately
        # This is a special case that needs edge metadata
        if ctx.node.type == NodeType.PERSON_JOB:
            await self._handle_person_job_first_execution(ctx)
        
        return ctx
    
    async def _handle_person_job_first_execution(self, ctx: PipelineContext) -> None:
        """Handle PersonJob first execution input mapping.
        
        This is a special case where PersonJob nodes can receive
        inputs only on their first execution. The mapping is determined
        by edge metadata.
        """
        # Check if this is the first execution
        if not self._is_first_execution(ctx):
            return
        
        # Process edges marked for first execution
        for edge in ctx.filtered_edges:
            if not edge.metadata:
                continue
                
            if edge.metadata.get('is_first_execution'):
                # Determine the template variable name
                if edge.metadata.get('label'):
                    # Use the arrow label as the template variable name
                    input_key = edge.metadata['label']
                else:
                    # No label, use "default" as the template variable name
                    input_key = 'default'
                
                # Store this mapping for the transform stage
                if not hasattr(ctx, 'input_mappings'):
                    ctx.input_mappings = {}
                ctx.input_mappings[edge] = input_key
    
    def _is_first_execution(self, ctx: PipelineContext) -> bool:
        """Check if this is the first execution of a node.
        
        A node is on its first execution if it has no prior completions
        in the execution context.
        """
        if not hasattr(ctx.context, 'completed_nodes'):
            return True
        
        node_id = str(ctx.node.id)
        return node_id not in ctx.context.completed_nodes