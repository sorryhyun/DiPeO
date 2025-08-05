"""Prepare node list from dynamically loaded spec files."""
import json
from typing import Any, Dict, List


def prepare_node_list_from_specs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node types from all loaded spec AST files and prepare for batch processing.
    
    Args:
        inputs: Dictionary containing loaded AST data from glob pattern
        
    Returns:
        Dictionary with items array for batch processing
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
        base_filename = filename.split('/')[-1]
        node_type = base_filename.replace('.spec.ts.json', '').replace('-', '_')
        
        # Verify the spec file contains valid node specification
        if isinstance(ast_data, dict):
            # Check if it has the expected structure
            constants = ast_data.get('constants', [])
            for const in constants:
                if const.get('name', '').endswith('Spec'):
                    # Found a valid node spec
                    node_types.append(node_type)
                    break
    
    if not node_types:
        raise ValueError("No node types found in spec files")
    
    print(f"Generating backend files for {len(node_types)} nodes from TypeScript specifications:")
    for nt in sorted(node_types):
        print(f"  - {nt}")
    
    # Create array of inputs for batch processing
    # Add 'default' wrapper to prevent unwrapping by runtime resolver
    result = {
        'default': {
            'items': [{'node_spec_path': node_type} for node_type in sorted(node_types)]
        }
    }
    
    return result