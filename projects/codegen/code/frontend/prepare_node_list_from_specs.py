"""Prepare node list from dynamically loaded spec files for frontend generation."""
import json
from typing import Any, Dict, List


def prepare_node_list_from_specs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract node types from loaded spec AST files and prepare for batch processing."""
    
    node_types = []
    
    # Handle case where db node passes data as 'default'
    # Also handle when code_job adds 'inputs' and 'node_id' keys
    if 'default' in inputs:
        # The actual data is in the 'default' key
        actual_data = inputs['default']
        # Check if this looks like the spec files (should be a dict with file paths as keys)
        if isinstance(actual_data, dict) and any(k.endswith('.spec.ts.json') for k in actual_data.keys()):
            inputs = actual_data
    
    for filename, ast_data in inputs.items():
        if filename == 'default' or not filename.endswith('.spec.ts.json'):
            continue
        
        base_filename = filename.split('/')[-1]
        node_type = base_filename.replace('.spec.ts.json', '').replace('-', '_')
        
        if isinstance(ast_data, dict):
            constants = ast_data.get('constants', [])
            for const in constants:
                # Check for both 'Spec' and 'spec' to handle camelCase naming
                name = const.get('name', '')
                if name.endswith('Spec') or name.endswith('spec'):
                    node_types.append(node_type)
                    break
    
    if not node_types:
        raise ValueError("No node types found in spec files")
    
    
    # Return the list directly - it will be placed under 'default' key
    # and batch executor will use batch_input_key='default' to find it
    result = [{'node_spec_path': node_type} for node_type in sorted(node_types)]
    
    return result