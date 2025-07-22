"""
Node specification loader for code generation.
"""

import json
import os
from typing import Dict, Any


def get_node_spec_path(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Get node spec path from inputs or use default."""
    print(f"DEBUG get_node_spec_path: Received inputs keys: {list(inputs.keys())}")
    
    # First check if inputs has a non-empty node_spec_path
    node_spec_path = inputs.get('node_spec_path', '')
    
    # Also check if it's nested under 'inputs' (from diagram execution)
    if not node_spec_path and 'inputs' in inputs:
        node_spec_path = inputs['inputs'].get('node_spec_path', '')
    
    # Also check if it's under default
    if not node_spec_path and 'default' in inputs:
        default_data = inputs['default']
        if isinstance(default_data, dict):
            node_spec_path = default_data.get('node_spec_path', '')
    
    # Use default if still empty
    if not node_spec_path:
        node_spec_path = 'files/codegen/specifications/nodes/sub_diagram.json'
    else:
        # If only a name is provided, construct the full path
        if not node_spec_path.endswith('.json') and not '/' in node_spec_path:
            node_spec_path = f'files/codegen/specifications/nodes/{node_spec_path}.json'
    
    result = {'node_spec_path': node_spec_path, 'default': {'node_spec_path': node_spec_path}}
    return result


def load_node_spec(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load a node specification JSON file."""

    # Get the file path from inputs
    # Check both direct and nested under 'default'
    node_spec_path = inputs.get('node_spec_path', '')
    if not node_spec_path and 'default' in inputs:
        node_spec_path = inputs['default'].get('node_spec_path', '')
    
    if not node_spec_path:
        return {"error": "No node_spec_path provided"}

    # Construct full path
    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    full_path = os.path.join(base_dir, node_spec_path)
    
    # Read the file
    try:
        with open(full_path, 'r') as f:
            spec_data = json.load(f)
        
        # Return the spec data wrapped in a default key for proper data flow
        result = {"default": spec_data}
        return result
    except FileNotFoundError:
        return {"error": f"File not found: {node_spec_path}"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in {node_spec_path}: {str(e)}"}