"""Prepare init context from dynamically loaded spec files."""
import ast
import json
from typing import Any, Dict, List


def prepare_init_context_from_specs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node types from all loaded spec AST files for __init__.py generation.
    
    Args:
        inputs: Dictionary containing loaded AST data from glob pattern
        
    Returns:
        Dictionary with node_types array for template
    """
    
    node_types = []
    
    # Handle case where db node passes data as 'default'
    if 'default' in inputs:
        default_value = inputs['default']
        if isinstance(default_value, str):
            # Parse the Python dict string to get the actual glob results
            try:
                # Try ast.literal_eval first (for Python dict format)
                inputs = ast.literal_eval(default_value)
            except (ValueError, SyntaxError):
                # If that fails, try JSON
                try:
                    inputs = json.loads(default_value)
                except json.JSONDecodeError:
                    # If both fail, treat as empty
                    inputs = {}
        elif isinstance(default_value, dict):
            inputs = default_value
    
    # Process each spec file
    for filename, ast_data in inputs.items():
        if filename == 'default' or not filename.endswith('.spec.ts.json'):
            continue
        
        # Extract node type from filename (e.g., "api-job.spec.ts.json" -> "api_job")
        base_filename = filename.split('/')[-1]
        node_type = base_filename.replace('.spec.ts.json', '').replace('-', '_')
        
        # Verify the spec file contains valid node specification
        if isinstance(ast_data, dict):
            # Check if it has the expected structure
            constants = ast_data.get('constants', [])
            for const in constants:
                # Check for both 'Spec' and 'spec' to handle camelCase naming
                name = const.get('name', '')
                if name.endswith('Spec') or name.endswith('spec'):
                    # Found a valid node spec
                    node_types.append(node_type)
                    break
    
    # print(f"Preparing to generate __init__.py for {len(node_types)} models")
    
    # Sort for consistent output
    node_types.sort()
    
    # Wrap in 'default' to prevent unwrapping by runtime resolver
    result = {
        'default': {
            'node_types': node_types
        }
    }
    
    return result