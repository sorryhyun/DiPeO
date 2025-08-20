"""Main API for domain-level input resolution.

This module provides the primary entry point for resolving node inputs during execution,
orchestrating all the domain resolution functions.
"""

from typing import Dict, Any
import json

from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableDiagram,
    ExecutableNode,
    StandardNodeOutput
)
from dipeo.domain.execution.transform_rules import DataTransformRules
from dipeo.domain.diagram.resolution.transformation_engine import StandardTransformationEngine

from .selectors import select_incoming_edges, compute_special_inputs
from .defaults import apply_defaults
from .errors import TransformationError, SpreadCollisionError


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
        transformed.setdefault(key, EnvelopeFactory.coerce(value))
    
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
    import logging
    logger = logging.getLogger(__name__)
    
    engine = StandardTransformationEngine()
    transformed: Dict[str, Envelope] = {}
    
    for edge in edges:
        # Get the output from source node
        source_output = ctx.get_node_output(edge.source_node_id)
        
        logger.debug(f"[Resolution] Edge {edge.source_node_id} -> {node.id}: output type={type(source_output).__name__ if source_output else 'None'}")
        
        if not source_output:
            logger.debug(f"[Resolution] No output from source node {edge.source_node_id}")
            continue
        
        # Extract value from output format
        value = extract_edge_value(source_output, edge)
        
        logger.debug(f"[Resolution] Extracted value type={type(value).__name__ if value is not None else 'None'}")
        if isinstance(value, dict) and len(value) <= 5:
            logger.debug(f"[Resolution] Value keys: {list(value.keys())}")
        
        if value is None:
            logger.debug(f"[Resolution] No value extracted from edge")
            continue
        
        # Get transformation rules (type-based + edge overrides)
        source_node = get_node_by_id(diagram, edge.source_node_id)
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
        
        # Handle packing mode (pack vs spread)
        packing_mode = getattr(edge, 'packing', 'pack') or 'pack'
        
        if packing_mode == 'spread':
            # Spread mode: merge dict keys into input namespace
            if not isinstance(transformed_value, dict):
                raise TransformationError(
                    f"Cannot use 'spread' packing with non-dict value. "
                    f"Value type: {type(transformed_value).__name__}"
                )
            
            # Check for key collisions
            conflicting_keys = [k for k in transformed_value.keys() if k in transformed]
            if conflicting_keys:
                raise SpreadCollisionError(
                    f"Spread operation would overwrite existing keys: {conflicting_keys}"
                )
            
            # Spread the dict values as individual Envelopes
            for key, val in transformed_value.items():
                transformed[key] = EnvelopeFactory.coerce(val)
        else:
            # Pack mode (default): bind to the input key
            input_key = edge.target_input or 'default'
            logger.debug(f"[Resolution] Pack mode: binding to input key '{input_key}'")
            transformed[input_key] = EnvelopeFactory.coerce(transformed_value)
    
    return transformed


def extract_edge_value(source_output: Any, edge: Any) -> Any:
    """Extract the actual value from a source node's output.
    
    Args:
        source_output: The output from the source node
        edge: The edge defining the connection
        
    Returns:
        The extracted value, or None if not available
    """
    # Handle Envelope format
    if isinstance(source_output, Envelope):
        # Extract based on content type
        if source_output.content_type == "raw_text":
            return str(source_output.body)
        elif source_output.content_type == "object":
            return source_output.body
        elif source_output.content_type == "conversation_state":
            return source_output.body
        elif source_output.content_type == "condition_result":
            # Special handling for condition outputs
            branch_taken = source_output.meta.get("branch_taken")
            branch_data = source_output.meta.get("branch_data", {})
            if branch_taken == "true":
                return {"condtrue": branch_data}
            else:
                return {"condfalse": branch_data}
        else:
            # Unknown content type - return body as-is
            return source_output.body
    
    # Handle StandardNodeOutput format
    if isinstance(source_output, StandardNodeOutput):
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


def get_node_by_id(diagram: ExecutableDiagram, node_id: str) -> ExecutableNode | None:
    """Get a node from the diagram by its ID.
    
    Args:
        diagram: The executable diagram
        node_id: The node ID to find
        
    Returns:
        The node if found, None otherwise
    """
    for node in diagram.nodes:
        if node.id == node_id:
            return node
    return None