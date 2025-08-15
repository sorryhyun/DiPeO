"""Transform stage - applies data transformations."""

from typing import Any
import json

from dipeo.core.resolution import StandardNodeOutput, StandardTransformationEngine
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from .base import PipelineStage, PipelineContext


class TransformStage(PipelineStage):
    """Applies transformations to edge values.
    
    This stage:
    1. Extracts values from StandardNodeOutput format
    2. Applies edge transformation rules
    3. Handles envelope content type conversions
    4. Maps values to input keys
    """
    
    def __init__(self):
        self.transformation_engine = StandardTransformationEngine()
    
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Apply transformations to filtered edge values."""
        
        for edge in ctx.filtered_edges:
            # Get the value for this edge
            value = ctx.get_edge_value(edge)
            if value is None:
                continue
            
            # Apply transformations
            transformed_value = self._apply_transformations(value, edge)
            
            if transformed_value is None:
                continue
            
            # Determine the input key for this value
            input_key = self._get_input_key(edge, ctx)
            
            # Store the transformed value
            ctx.transformed_values[input_key] = transformed_value
        
        return ctx
    
    def _apply_transformations(self, value: Any, edge) -> Any:
        """Apply transformation rules from edge to value."""
        
        # Handle StandardNodeOutput
        if isinstance(value, StandardNodeOutput):
            output_key = edge.source_output or "default"
            
            # Extract the actual value based on output key
            if not isinstance(value.value, dict):
                # Non-dict values are wrapped
                output_dict = {"default": value.value}
            else:
                output_dict = value.value
            
            if output_key in output_dict:
                actual_value = output_dict[output_key]
            elif output_key == "default":
                # Special handling for default output
                if len(output_dict) == 1:
                    # If requesting default and only one output, use it
                    actual_value = next(iter(output_dict.values()))
                elif "default" in output_dict:
                    # Use explicit default key
                    actual_value = output_dict["default"]
                else:
                    # For multi-output cases, use the entire dict
                    actual_value = output_dict
            else:
                # No matching output
                return None
        else:
            actual_value = value
        
        # Apply transformation rules if edge has them
        if hasattr(edge, 'transform_rules') and edge.transform_rules:
            actual_value = self.transformation_engine.transform(
                actual_value,
                edge.transform_rules
            )
        
        return actual_value
    
    def _get_input_key(self, edge, ctx: PipelineContext) -> str:
        """Determine the input key for an edge value."""
        
        # Check if we have a special mapping for this edge
        if hasattr(ctx, 'input_mappings') and edge in ctx.input_mappings:
            return ctx.input_mappings[edge]
        
        # Use edge's target input or default
        return edge.target_input or 'default'
    
    async def transform_envelope(self, envelope: Envelope, edge, target_node) -> Envelope:
        """Apply edge transformations to envelope (for envelope-based flow)."""
        
        # Check if transformation needed based on edge transform_rules
        if hasattr(edge, 'transform_rules') and edge.transform_rules:
            # Handle common transformations
            if 'json_to_text' in edge.transform_rules:
                if envelope.content_type == "object":
                    text = json.dumps(envelope.body)
                    return EnvelopeFactory.text(
                        text,
                        produced_by=envelope.produced_by,
                        trace_id=envelope.trace_id
                    ).with_meta(**envelope.meta)
            
            elif 'text_to_json' in edge.transform_rules:
                if envelope.content_type == "raw_text":
                    try:
                        data = json.loads(envelope.body)
                        return EnvelopeFactory.json(
                            data,
                            produced_by=envelope.produced_by,
                            trace_id=envelope.trace_id
                        ).with_meta(**envelope.meta)
                    except json.JSONDecodeError:
                        # Keep as text if not valid JSON
                        pass
        
        return envelope