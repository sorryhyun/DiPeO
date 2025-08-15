"""Defaults stage - applies default values for missing inputs."""

from typing import Any

from .base import PipelineStage, PipelineContext


class DefaultsStage(PipelineStage):
    """Applies default values for unconnected or missing inputs.
    
    This stage:
    1. Identifies required inputs that are missing
    2. Applies node-specific default values
    3. Merges all inputs into final result
    """
    
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Apply defaults and produce final inputs."""
        
        # Start with transformed values
        ctx.final_inputs = dict(ctx.transformed_values)
        
        # Add special inputs (they don't override regular inputs)
        for key, value in ctx.special_inputs.items():
            if key not in ctx.final_inputs:
                ctx.final_inputs[key] = value
        
        # Apply defaults for missing required inputs
        self._apply_defaults(ctx)
        
        # Validate the final inputs
        self._validate_inputs(ctx)
        
        return ctx
    
    def _apply_defaults(self, ctx: PipelineContext) -> None:
        """Apply default values for missing inputs."""
        
        # Check if node has required inputs defined
        if hasattr(ctx.node, 'required_inputs'):
            for required_input in ctx.node.required_inputs:
                if required_input not in ctx.final_inputs:
                    # Get default value for this input
                    default_value = self._get_default_value(
                        ctx.node, 
                        required_input
                    )
                    if default_value is not None:
                        ctx.final_inputs[required_input] = default_value
        
        # Apply node-type specific defaults
        self._apply_node_specific_defaults(ctx)
    
    def _get_default_value(self, node, input_name: str) -> Any:
        """Get default value for a specific input."""
        
        # Check if node has default values defined
        if hasattr(node, 'default_values'):
            defaults = node.default_values
            if isinstance(defaults, dict) and input_name in defaults:
                return defaults[input_name]
        
        # Check for input type-based defaults
        if hasattr(node, 'input_types'):
            input_type = node.input_types.get(input_name)
            if input_type:
                return self._get_type_default(input_type)
        
        # Default to None for most inputs
        return None
    
    def _get_type_default(self, input_type: str) -> Any:
        """Get default value based on input type."""
        
        type_defaults = {
            'string': '',
            'number': 0,
            'boolean': False,
            'array': [],
            'object': {},
            'null': None,
        }
        
        return type_defaults.get(input_type, None)
    
    def _apply_node_specific_defaults(self, ctx: PipelineContext) -> None:
        """Apply defaults specific to certain node types."""
        
        # Add node-type specific default logic here
        # For example, certain nodes might have special default behaviors
        pass
    
    def _validate_inputs(self, ctx: PipelineContext) -> None:
        """Validate that all required inputs are present."""
        
        errors = []
        
        # Check required inputs
        if hasattr(ctx.node, 'required_inputs'):
            for required in ctx.node.required_inputs:
                if required not in ctx.final_inputs or ctx.final_inputs[required] is None:
                    errors.append(f"Missing required input: {required}")
        
        # Store validation errors in context
        if errors:
            if not hasattr(ctx, 'validation_errors'):
                ctx.validation_errors = []
            ctx.validation_errors.extend(errors)