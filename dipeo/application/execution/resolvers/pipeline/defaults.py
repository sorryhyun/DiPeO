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
        """Apply default values for missing inputs.
        
        SEAC: Only apply declared port defaults, no type-based or global fallbacks.
        """
        
        # Only apply explicitly declared port defaults
        if hasattr(ctx.node, 'input_ports'):
            # Node has port specifications
            for port in ctx.node.input_ports:
                port_name = port.get('name', 'default')
                
                # Check if this port has a value
                if port_name not in ctx.final_inputs:
                    # Only apply if port has an explicit default value
                    if 'default' in port:
                        ctx.final_inputs[port_name] = port['default']
                    elif port.get('required', False):
                        # Required port with no value and no default - this will be caught in validation
                        pass
        
        # Check if node has legacy default_values defined (backward compatibility)
        elif hasattr(ctx.node, 'default_values'):
            defaults = ctx.node.default_values
            if isinstance(defaults, dict):
                for input_name, default_value in defaults.items():
                    if input_name not in ctx.final_inputs:
                        ctx.final_inputs[input_name] = default_value
    
    def _get_default_value(self, node, input_name: str) -> Any:
        """Get default value for a specific input.
        
        SEAC: Only returns explicitly declared defaults, no type-based guessing.
        """
        
        # Check if node has port specifications
        if hasattr(node, 'input_ports'):
            for port in node.input_ports:
                if port.get('name', 'default') == input_name:
                    return port.get('default')
        
        # Check if node has legacy default values defined
        if hasattr(node, 'default_values'):
            defaults = node.default_values
            if isinstance(defaults, dict) and input_name in defaults:
                return defaults[input_name]
        
        # No default found
        return None
    
    def _get_type_default(self, input_type: str) -> Any:
        """DEPRECATED: Type-based defaults are no longer used in SEAC.
        
        This method is kept for backward compatibility but should not be used.
        """
        return None
    
    def _apply_node_specific_defaults(self, ctx: PipelineContext) -> None:
        """DEPRECATED: Node-specific default logic removed in SEAC.
        
        All defaults should be declared in port specifications.
        """
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