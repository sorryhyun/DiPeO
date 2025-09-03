"""Main API for domain-level input resolution.

This module provides the primary entry point for resolving node inputs during execution,
orchestrating all the domain resolution functions.
"""

from typing import Dict, Any
import json
import logging

from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableDiagram,
    ExecutableNode,
    StandardNodeOutput
)
from dipeo.domain.execution.transform_rules import DataTransformRules
from dipeo.diagram_generated import ContentType

from .transformation_engine import StandardTransformationEngine
from .selectors import select_incoming_edges, compute_special_inputs
from .defaults import apply_defaults
from .errors import TransformationError, SpreadCollisionError

logger = logging.getLogger(__name__)


def resolve_inputs(
    node: ExecutableNode,
    diagram: ExecutableDiagram,
    ctx: ExecutionContext
) -> Dict[str, Envelope]:
    """Resolve all inputs for a node during execution.
    
    This is the main orchestration function that:
    1. Selects ready edges
    2. Fetches and transforms values
    3. Handles special inputs
    4. Applies defaults
    5. Validates final inputs
    
    Args:
        node: The node to resolve inputs for
        diagram: The executable diagram containing the node
        ctx: Execution context with node states and outputs
        
    Returns:
        Dictionary mapping input keys to Envelope values
        
    Raises:
        TransformationError: If transformation fails
        SpreadCollisionError: If spread operations collide
        InputResolutionError: If required inputs are missing
    """
    # 1) Select edges that are ready to contribute values
    edges = select_incoming_edges(diagram, node, ctx)
    
    # 2) Fetch and transform values from source nodes
    transformed = transform_edge_values(edges, node, diagram, ctx)
    
    # 3) Add special inputs that don't come from edges
    special = compute_special_inputs(node, ctx)
    for key, value in special.items():
        # Special inputs don't override explicit edge inputs
        if isinstance(value, str):
            transformed.setdefault(key, EnvelopeFactory.text(value))
        else:
            transformed.setdefault(key, EnvelopeFactory.json(value))
    
    # 4) Apply defaults for missing required inputs
    final_inputs = apply_defaults(node, transformed)
    
    return final_inputs


def transform_edge_values(
    edges: list,
    node: ExecutableNode,
    diagram: ExecutableDiagram,
    ctx: ExecutionContext
) -> Dict[str, Envelope]:
    """Transform values from edges into node inputs.
    
    Args:
        edges: List of edges to process
        node: Target node receiving the inputs
        diagram: The executable diagram
        ctx: Execution context
        
    Returns:
        Dictionary of transformed input values as Envelopes
        
    Raises:
        TransformationError: If transformation fails
        SpreadCollisionError: If spread operations collide
    """
    engine = StandardTransformationEngine()
    transformed: Dict[str, Envelope] = {}
    
    for edge in edges:
        # Get the output from source node
        source_output = ctx.get_node_output(edge.source_node_id)
        
        if not source_output:
            continue
        
        # Extract value from output format
        value = extract_edge_value(source_output, edge)
        
        if value is None:
            continue
        
        # Handle edge content_type transformation
        if hasattr(edge, 'content_type') and edge.content_type:
            if edge.content_type == ContentType.RAW_TEXT:
                # Extract text content from complex structures
                if isinstance(value, dict):
                    # Try 'default' key first, then any string value
                    if 'default' in value:
                        value = value['default']
                    else:
                        # Find the first string value in the dict
                        string_val = next(
                            (v for v in value.values() if isinstance(v, str)), 
                            None
                        )
                        if string_val:
                            value = string_val
                        else:
                            # If no string found, convert the whole dict to string
                            value = str(value)
                # Ensure it's a string
                value = str(value)
            elif edge.content_type == ContentType.OBJECT:
                # Keep as-is for object type
                pass
            elif edge.content_type == ContentType.CONVERSATION_STATE:
                # Keep as-is for conversation state
                pass
        
        # Get transformation rules (type-based + edge overrides)
        source_node = diagram.get_node(edge.source_node_id)
        if not source_node:
            continue
        
        type_rules = DataTransformRules.get_data_transform(source_node, node)
        
        # Merge with edge-specific transform rules if present
        edge_rules = getattr(edge, 'transform_rules', {}) or {}
        rules = DataTransformRules.merge_transforms(edge_rules, type_rules)
        
        # Apply transformations
        try:
            if rules:
                transformed_value = engine.transform(value, rules)
            else:
                transformed_value = value
        except Exception as ex:
            raise TransformationError(
                f"Failed to transform value from {edge.source_node_id} to {edge.target_node_id}: {str(ex)}"
            ) from ex
        
        # Unified packing behavior based on edge labeling
        # Unlabeled edges pass data as-is under 'default' key
        # Labeled edges pack data under the specified label
        key = edge.target_input or 'default'
        
        # Create appropriate envelope based on value type
        env = transformed_value if isinstance(transformed_value, Envelope) else (
            EnvelopeFactory.text(transformed_value) if isinstance(transformed_value, str)
            else EnvelopeFactory.json(transformed_value)
        )
        transformed[key] = env
    
    return transformed


def extract_edge_value(source_output: Any, edge: Any) -> Any:
    """Extract the actual value from a source node's output.
    
    Priority order:
    1. Envelope representations (if content_type specified)
    2. Envelope body based on content_type
    3. StandardNodeOutput (deprecated, with warning)
    4. Raw dict/value (backward compatibility)
    
    Args:
        source_output: The output from the source node
        edge: The edge defining the connection
        
    Returns:
        The extracted value, or None if not available
    """
    # Handle Envelope format (PREFERRED)
    if isinstance(source_output, Envelope):
        # Priority 1: Use representations when available and content_type specified
        if hasattr(edge, 'content_type') and edge.content_type:
            if source_output.representations:
                # Map ContentType to representation key
                repr_mapping = {
                    ContentType.RAW_TEXT: "text",
                    ContentType.OBJECT: "object",
                    ContentType.CONVERSATION_STATE: "conversation"
                }
                
                repr_key = repr_mapping.get(edge.content_type)
                if repr_key and repr_key in source_output.representations:
                    logger.debug(
                        f"Using '{repr_key}' representation for edge "
                        f"{edge.source_node_id} -> {edge.target_node_id}"
                    )
                    return source_output.representations[repr_key]
                elif repr_key:
                    # Log warning for missing expected representation
                    logger.warning(
                        f"Edge requested '{repr_key}' representation but envelope "
                        f"only has: {list(source_output.representations.keys())}. "
                        f"Falling back to body."
                    )
        
        # Priority 2: Fallback to body based on envelope content_type
        if source_output.content_type == "raw_text":
            return str(source_output.body)
        elif source_output.content_type == "object":
            return source_output.body
        elif source_output.content_type == "conversation_state":
            return source_output.body
        else:
            # Unknown content type - return body as-is
            return source_output.body
    
    # Handle StandardNodeOutput format (DEPRECATED)
    if isinstance(source_output, StandardNodeOutput):
        logger.debug(
            f"Edge {edge.source_node_id} -> {edge.target_node_id} using deprecated "
            f"StandardNodeOutput. Consider migrating to Envelope with representations."
        )
        
        output_key = edge.source_output or "default"
        
        # Check if this is structured output
        is_structured = source_output.metadata.get("is_structured", False)
        
        # Extract the actual value
        if not isinstance(source_output.value, dict):
            # Non-dict values are wrapped
            output_dict = {"default": source_output.value}
        else:
            output_dict = source_output.value
        
        if output_key in output_dict:
            return output_dict[output_key]
        elif output_key == "default":
            # Special handling for default output
            if is_structured:
                # Preserve full structure
                return source_output.value
            elif "default" in output_dict:
                return output_dict["default"]
            else:
                # Return entire dict for single-key dicts
                return output_dict
        else:
            # No matching output
            return None
    
    # Handle dict format (backward compatibility)
    if isinstance(source_output, dict):
        if "value" in source_output:
            return source_output["value"]
        # Return dict as-is
        return source_output
    
    # Return raw value
    return source_output


