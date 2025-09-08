"""Main API for domain-level input resolution.

This module provides the primary entry point for resolving node inputs during execution,
orchestrating all the domain resolution functions.
"""

import logging
import os
from typing import Any

from dipeo.diagram_generated import ContentType
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.execution.transform_rules import DataTransformRules

from .defaults import apply_defaults
from .errors import TransformationError
from .selectors import compute_special_inputs, select_incoming_edges
from .transformation_engine import StandardTransformationEngine

logger = logging.getLogger(__name__)
STRICT_IO = os.getenv("DIPEO_LOOSE_EDGE_VALUE", "0") != "1"


def resolve_inputs(
    node: ExecutableNode, diagram: ExecutableDiagram, ctx: ExecutionContext
) -> dict[str, Envelope]:
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
            transformed.setdefault(key, EnvelopeFactory.create(body=value))
        else:
            transformed.setdefault(key, EnvelopeFactory.create(body=value))

    # 4) Apply defaults for missing required inputs
    final_inputs = apply_defaults(node, transformed)

    return final_inputs


def transform_edge_values(
    edges: list, node: ExecutableNode, diagram: ExecutableDiagram, ctx: ExecutionContext
) -> dict[str, Envelope]:
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
    transformed: dict[str, Envelope] = {}

    for edge in edges:
        # Get the output from source node
        source_output = ctx.state.get_node_output(edge.source_node_id)

        if not source_output:
            continue

        # Extract value from output format
        value = extract_edge_value(source_output, edge)

        if value is None:
            continue

        # Handle edge content_type transformation
        if hasattr(edge, "content_type") and edge.content_type:
            if edge.content_type == ContentType.RAW_TEXT:
                # Extract text content from complex structures
                if isinstance(value, dict):
                    # Try 'default' key first, then any string value
                    if "default" in value:
                        value = value["default"]
                    else:
                        # Find the first string value in the dict
                        string_val = next((v for v in value.values() if isinstance(v, str)), None)
                        value = string_val or str(value)
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
        edge_rules = getattr(edge, "transform_rules", {}) or {}
        rules = DataTransformRules.merge_transforms(edge_rules, type_rules)

        # Apply transformations
        try:
            transformed_value = engine.transform(value, rules) if rules else value
        except Exception as ex:
            raise TransformationError(
                f"Failed to transform value from {edge.source_node_id} to {edge.target_node_id}: {ex!s}"
            ) from ex

        # Unified packing behavior based on edge labeling
        # Unlabeled edges pass data as-is under 'default' key
        # Labeled edges pack data under the specified label
        key = edge.target_input or "default"

        # Create appropriate envelope based on value type
        env = (
            transformed_value
            if isinstance(transformed_value, Envelope)
            else (
                EnvelopeFactory.create(body=transformed_value)
                if isinstance(transformed_value, str)
                else EnvelopeFactory.create(body=transformed_value)
            )
        )
        transformed[key] = env

    return transformed


def extract_edge_value(source_output: Any, edge: Any) -> Any:
    """Extract the value from a source node's output with smart conversions.

    Handles natural data flow with automatic conversions based on edge needs:
    - Any → RAW_TEXT (via str() or json.dumps())
    - JSON string → OBJECT (via json.loads())
    - Any → CONVERSATION_STATE (wrap if needed)

    Args:
        source_output: The output from the source node
        edge: The edge defining the connection

    Returns:
        The extracted value, or None if not available
    """
    import json

    if isinstance(source_output, Envelope):
        desired = getattr(edge, "content_type", None)
        actual = source_output.content_type
        body = source_output.body

        if desired is None:
            return body

        # Exact match - no conversion needed
        if desired == actual:
            return body

        # Smart conversions based on edge needs

        # 1. Any → RAW_TEXT conversion (always allowed)
        if desired == ContentType.RAW_TEXT:
            logger.debug(f"Converting {actual} → RAW_TEXT")
            if actual in (ContentType.OBJECT, ContentType.CONVERSATION_STATE):
                # Pretty-print JSON data
                try:
                    return (
                        json.dumps(body, indent=2) if isinstance(body, dict | list) else str(body)
                    )
                except (TypeError, ValueError):
                    return str(body)
            else:
                # Any other type can be converted to text
                return str(body) if body is not None else ""

        # 2. RAW_TEXT → OBJECT conversion (parse JSON)
        if desired == ContentType.OBJECT:
            if actual == ContentType.RAW_TEXT and isinstance(body, str):
                logger.debug("Converting RAW_TEXT → OBJECT via JSON parsing")
                try:
                    # Try to parse JSON string
                    parsed = json.loads(body)
                    return parsed
                except (json.JSONDecodeError, ValueError):
                    # If not valid JSON, wrap in dict
                    logger.debug("RAW_TEXT is not valid JSON, wrapping in dict")
                    return {"text": body}
            elif actual == ContentType.CONVERSATION_STATE:
                # Conversation state is already a dict/object
                logger.debug("Converting CONVERSATION_STATE → OBJECT (pass-through)")
                return body
            elif not STRICT_IO:
                logger.debug(f"Loose mode: allowing {actual} → OBJECT")
                return body

        # 3. Any → CONVERSATION_STATE conversion
        if desired == ContentType.CONVERSATION_STATE:
            logger.debug(f"Converting {actual} → CONVERSATION_STATE")
            if actual == ContentType.CONVERSATION_STATE:
                return body
            elif actual == ContentType.OBJECT and isinstance(body, dict):
                # Object that's already a dict can be used as conversation state
                return body
            else:
                # Wrap any other type in conversation structure
                logger.debug(f"Wrapping {actual} in conversation structure")
                return {
                    "messages": [{"role": "assistant", "content": str(body)}] if body else [],
                    "context": {},
                }

        # 4. BINARY type - no automatic conversions
        if desired == ContentType.BINARY or actual == ContentType.BINARY:
            if desired != actual:
                raise TypeError(
                    f"Cannot convert between BINARY and {actual if desired == ContentType.BINARY else desired}. "
                    f"Binary data must be explicitly handled."
                )

        # If no conversion was applied and we're in strict mode, raise error
        if STRICT_IO:
            raise TypeError(
                f"Edge expects {desired}, but upstream produced {actual}. "
                f"Cannot auto-convert in strict mode. "
                f"To allow legacy coercions, set DIPEO_LOOSE_EDGE_VALUE=1."
            )
        else:
            # Loose mode fallback
            logger.debug(f"Loose mode: allowing {actual} → {desired} (returning body as-is)")
            return body

    # Legacy dicts: only if loose mode is enabled
    if isinstance(source_output, dict):
        if not STRICT_IO:
            logger.debug("Loose mode: handling legacy dict output")
            return source_output.get("value", source_output)
        raise TypeError("Expected Envelope; got raw dict. Wrap outputs in Envelope.")

    # Return raw value
    logger.debug(f"Returning raw value of type {type(source_output)}")
    return source_output
