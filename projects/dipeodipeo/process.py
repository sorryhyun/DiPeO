"""Process generated DiPeO diagrams to clean up and format the output."""

from io import StringIO
from typing import Any

import yaml


# Custom YAML representer for better multiline string formatting
class LiteralScalarString(str):
    """A string that should be represented as a literal block scalar in YAML."""

    pass


def literal_scalar_representer(dumper, data):
    """Represent a string as a literal block scalar (|) in YAML."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


def _remove_nulls_and_empty(obj):
    """Recursively remove null values and empty collections from dictionaries and lists."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            # Skip empty persons field
            if k == "persons" and (v is None or (isinstance(v, dict) and not v)):
                continue
            cleaned_value = _remove_nulls_and_empty(v)
            if cleaned_value is not None:
                cleaned[k] = cleaned_value
        return cleaned if cleaned else None
    elif isinstance(obj, list):
        cleaned = [_remove_nulls_and_empty(item) for item in obj if item is not None]
        return cleaned if cleaned else None
    else:
        return obj


def _fix_code_fields(diagram):
    """Convert code fields to use literal scalar format for better readability."""
    if "nodes" in diagram:
        for node in diagram["nodes"]:
            if "props" in node and isinstance(node["props"], dict):
                if "code" in node["props"] and isinstance(node["props"]["code"], str):
                    # Replace escaped newlines with actual newlines
                    code = node["props"]["code"].replace("\\n", "\n")
                    # Ensure code ends with newline to get | instead of |-
                    if not code.endswith("\n"):
                        code += "\n"
                    # Mark as literal scalar string for YAML formatting
                    node["props"]["code"] = LiteralScalarString(code)
    return diagram


def _extract_diagram_from_inputs(inputs: dict[str, Any]) -> dict:
    """Extract and parse the diagram from the inputs."""
    generated_diagram = inputs.get("generated_diagram", {})
    diagram_yaml_string = generated_diagram["output"][1]["content"][0]["text"]

    # Parse the YAML string to extract metadata
    diagram_dict = yaml.safe_load(diagram_yaml_string)
    return diagram_dict["diagram"]


def _create_ordered_diagram(diagram: dict) -> dict:
    """Create an ordered diagram with preferred key ordering."""
    key_order = ["version", "name", "description", "persons", "nodes", "connections"]

    # Create ordered diagram with version first
    ordered_diagram = {}
    for key in key_order:
        if key in diagram:
            ordered_diagram[key] = diagram[key]

    # Add any remaining keys not in our preferred order
    for key in diagram:
        if key not in ordered_diagram:
            ordered_diagram[key] = diagram[key]

    return ordered_diagram


def _format_yaml_output(ordered_diagram: dict) -> str:
    """Format the diagram as YAML with proper formatting."""
    # Create custom YAML dumper
    yaml_dumper = yaml.SafeDumper
    yaml_dumper.add_representer(LiteralScalarString, literal_scalar_representer)

    # Generate YAML string with proper formatting
    stream = StringIO()
    yaml.dump(
        ordered_diagram,
        stream,
        Dumper=yaml_dumper,
        default_flow_style=False,
        sort_keys=False,  # Preserve our key order
        allow_unicode=True,
        width=120,
    )  # Wider lines for better code formatting

    return stream.getvalue()


def process_diagram(inputs: dict[str, Any]) -> str:
    """
    Process a generated diagram to remove nulls, reorder keys, and format as YAML.

    Args:
        inputs: Dictionary containing the generated diagram

    Returns:
        String with the formatted YAML output
    """
    # Extract the diagram from inputs
    diagram = _extract_diagram_from_inputs(inputs)

    # Remove null values and empty persons
    diagram = _remove_nulls_and_empty(diagram)

    # Fix code fields for proper multiline formatting
    diagram = _fix_code_fields(diagram)

    # Create ordered diagram
    ordered_diagram = _create_ordered_diagram(diagram)

    # Format as YAML
    return _format_yaml_output(ordered_diagram)
