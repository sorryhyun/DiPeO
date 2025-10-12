"""Utility functions for Python diagram compilation."""

import re
from typing import Any

from dipeo.diagram_generated.domain_models import DomainDiagram


def interpolate_prompt(
    prompt: str,
    node: Any,
    diagram: DomainDiagram,
    node_outputs: dict[str, str],
) -> str:
    """Interpolate {{variable}} patterns in prompt with actual variable references.

    Looks up incoming edges to find variable names (from edge labels or source node names).
    Converts template string to f-string format.

    Args:
        prompt: The prompt string containing {{variable}} patterns
        node: The node whose prompt is being interpolated
        diagram: The full diagram containing all nodes and arrows
        node_outputs: Mapping of node IDs to their output variable names

    Returns:
        Interpolated prompt string ready for f-string formatting
    """
    # Find all {{variable}} patterns
    pattern = r"\{\{(\w+)\}\}"
    matches = re.findall(pattern, prompt)

    if not matches:
        return prompt

    # Build mapping of variable names to Python variable references
    var_mapping = {}
    incoming_arrows = [a for a in diagram.arrows if a.target.startswith(f"{node.id}_")]

    for var_name in matches:
        # Look for edge with matching label
        edge = next(
            (a for a in incoming_arrows if hasattr(a, "label") and a.label == var_name), None
        )

        if edge:
            # Extract source node ID from edge.source (format: "node_id_output_handle")
            source_handle = edge.source
            source_node_id = (
                "_".join(source_handle.split("_")[:-2]) if "_" in source_handle else source_handle
            )
            # Get the source node's output variable
            var_mapping[var_name] = node_outputs.get(source_node_id, var_name)

        else:
            # No edge found - use variable name as-is
            var_mapping[var_name] = var_name

    # Convert {{variable}} to {variable} for f-string
    interpolated = prompt
    for var_name, py_var in var_mapping.items():
        interpolated = interpolated.replace(f"{{{{{var_name}}}}}", f"{{{py_var}}}")

    return interpolated


def node_var_name(node: Any) -> str:
    """Generate a valid Python variable name for a node's output.

    Args:
        node: The node to generate a variable name for

    Returns:
        A valid Python variable name based on the node's label
    """
    label = (
        node.data.get("label", "node") if hasattr(node, "data") else getattr(node, "label", "node")
    )
    # Clean label to make valid Python variable name
    var_name = label.lower().replace(" ", "_").replace("~", "_")
    var_name = "".join(c if c.isalnum() or c == "_" else "_" for c in var_name)
    return var_name + "_output"


def indent_string(level: int) -> str:
    """Get indentation string for the given level.

    Args:
        level: Indentation level (0-based)

    Returns:
        Indentation string (4 spaces per level)
    """
    return "    " * level
