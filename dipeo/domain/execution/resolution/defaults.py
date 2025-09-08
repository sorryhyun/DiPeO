"""Default value application for domain-level input resolution.

This module uses the constraint system to apply default values for missing required inputs.
"""

from typing import Any

from dipeo.domain.diagram.models.executable_diagram import ExecutableNode
from dipeo.domain.diagram.validation.constraints import GeneratedConstraints
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .errors import InputResolutionError


def apply_defaults(
    node: ExecutableNode, partial_inputs: dict[str, Envelope]
) -> dict[str, Envelope]:
    """Apply default values for missing required inputs.

    Uses the GeneratedConstraints to determine required handles for the node type,
    and applies default values or raises errors for missing required inputs.

    Args:
        node: The node to apply defaults for
        partial_inputs: Current input values as Envelopes

    Returns:
        Dictionary with defaults applied for missing inputs

    Raises:
        InputResolutionError: If required inputs are missing with no defaults
    """
    from dipeo.diagram_generated import NodeType

    final_inputs = dict(partial_inputs)

    # START nodes don't require inputs (they have max_inputs=0)
    if node.type == NodeType.START:
        # START nodes generate output, don't need inputs
        return final_inputs

    # Get constraints for this node type
    constraints = GeneratedConstraints.get_constraint(node.type)

    if not constraints:
        # No constraints defined, return inputs as-is
        return final_inputs

    # Note: required_handles in constraints define OUTPUT requirements, not input requirements
    # For input requirements, we need to look at node-specific configuration

    # Check if node has explicitly required inputs (from node configuration)
    if hasattr(node, "required_inputs"):
        for required_input in node.required_inputs:
            if required_input not in final_inputs:
                # Try to get default value
                default_value = get_node_default(node, required_input)
                if default_value is not None:
                    if isinstance(default_value, str):
                        final_inputs[required_input] = EnvelopeFactory.create(body=default_value)
                    else:
                        final_inputs[required_input] = EnvelopeFactory.create(body=default_value)
                else:
                    raise InputResolutionError(
                        f"Missing required input '{required_input}' for node '{node.id}' of type '{node.type}'"
                    )

    # Apply any additional port-specific defaults
    apply_port_defaults(node, final_inputs)

    return final_inputs


def get_node_default(node: ExecutableNode, input_key: str) -> Any:
    """Get default value for a specific input from node definition.

    Args:
        node: The node to get defaults from
        input_key: The input key to get default for

    Returns:
        Default value if defined, None otherwise
    """
    # Check if node has port specifications
    if hasattr(node, "input_ports"):
        for port in node.input_ports:
            port_name = port.get("name", "default")
            if port_name == input_key and "default" in port:
                return port["default"]

    # Check if node has legacy default_values (backward compatibility)
    if hasattr(node, "default_values"):
        defaults = node.default_values
        if isinstance(defaults, dict) and input_key in defaults:
            return defaults[input_key]

    # Check if node has inline defaults in config
    if hasattr(node, "config") and isinstance(node.config, dict):
        config_defaults = node.config.get("defaults", {})
        if input_key in config_defaults:
            return config_defaults[input_key]

    return None


def is_handle_required(
    node: ExecutableNode, handle_key: str, current_inputs: dict[str, Envelope]
) -> bool:
    """Check if a handle is truly required given the current inputs.

    Some handles are conditionally required based on node type and other inputs.

    Args:
        node: The node to check
        handle_key: The handle key to check
        current_inputs: Currently provided inputs

    Returns:
        True if the handle is required, False otherwise
    """
    from dipeo.diagram_generated import NodeType

    # PersonJob "first" input is only required if no default input provided
    if node.type == NodeType.PERSON_JOB and handle_key == "first":
        # Not required if default input is provided
        if "default" in current_inputs:
            return False

    # Condition node handles are conditionally required
    if node.type == NodeType.CONDITION:
        # condtrue/condfalse are output handles, not input requirements
        if handle_key in ["condtrue", "condfalse"]:
            return False

    # By default, required handles are required
    return True


def apply_port_defaults(node: ExecutableNode, inputs: dict[str, Envelope]) -> None:
    """Apply additional port-specific defaults.

    This mutates the inputs dictionary to add port defaults.

    Args:
        node: The node with port definitions
        inputs: Current inputs dictionary (will be mutated)
    """
    # Apply port-specific defaults that aren't in required handles
    if hasattr(node, "input_ports"):
        for port in node.input_ports:
            port_name = port.get("name", "default")

            # Skip if already has value
            if port_name in inputs:
                continue

            # Apply default if defined
            if "default" in port:
                default_val = port["default"]
                if isinstance(default_val, str):
                    inputs[port_name] = EnvelopeFactory.create(body=default_val)
                else:
                    inputs[port_name] = EnvelopeFactory.create(body=default_val)
