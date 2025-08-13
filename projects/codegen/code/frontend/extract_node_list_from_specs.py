"""Extract node list from dynamically loaded spec files."""
import json
from typing import Any, Dict, List


def extract_node_list_from_specs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node types from all loaded spec AST files.
    
    Args:
        inputs: Dictionary containing loaded AST data from glob pattern
        
    Returns:
        Dictionary with node_list array
    """
    
    node_types = []
    
    # Handle case where db node passes data as 'default'
    if 'default' in inputs and len(inputs) == 1:
        inputs = inputs['default']
    
    # Process each spec file
    for filename, ast_data in inputs.items():
        if filename == 'default' or not filename.endswith('.spec.ts.json'):
            continue
        
        # Extract node type from filename (e.g., "api-job.spec.ts.json" -> "api_job")
        # Remove any path prefix if present
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
    
    # print(f"Found {len(node_types)} node types: {node_types}")
    
    # Sort for consistent output
    node_types.sort()
    
    # print(f"Nodes to register: {node_types}")
    
    return {'node_list': node_types}