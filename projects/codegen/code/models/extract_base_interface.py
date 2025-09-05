"""Extract BaseNodeData interface from TypeScript AST."""
import json
from typing import Any


def extract_base_interface(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract BaseNodeData interface from parsed TypeScript AST.

    Args:
        inputs: Dictionary containing diagram_ast data

    Returns:
        Dictionary with base_interface and found flag
    """
    # Parse AST data
    ast_data = inputs.get('diagram_ast', {})

    # Handle case where input is a list (from db node with multiple sources)
    if isinstance(ast_data, list) and ast_data:
        ast_data = ast_data[0] if isinstance(ast_data[0], dict) else json.loads(ast_data[0])
    elif isinstance(ast_data, str):
        ast_data = json.loads(ast_data)

    # Find BaseNodeData interface
    base_interface: dict[str, Any] | None = None
    for iface in ast_data.get('interfaces', []):
        if iface.get('name') == 'BaseNodeData':
            base_interface = iface
            break

    result = {
        'base_interface': base_interface,
        'found': base_interface is not None
    }

    return result
