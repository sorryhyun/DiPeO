"""Prepare node list from dynamically loaded spec files for frontend generation."""
import json
from typing import Any, Dict, List


def prepare_node_list_from_specs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract node types from loaded spec AST files and prepare for batch processing."""
    
    node_types = []
    
    if 'default' in inputs and len(inputs) == 1:
        inputs = inputs['default']
    
    for filename, ast_data in inputs.items():
        if filename == 'default' or not filename.endswith('.spec.ts.json'):
            continue
        
        base_filename = filename.split('/')[-1]
        node_type = base_filename.replace('.spec.ts.json', '').replace('-', '_')
        
        if isinstance(ast_data, dict):
            constants = ast_data.get('constants', [])
            for const in constants:
                if const.get('name', '').endswith('Spec'):
                    node_types.append(node_type)
                    break
    
    if not node_types:
        raise ValueError("No node types found in spec files")
    
    
    result = {
        'items': [{'node_spec_path': node_type} for node_type in sorted(node_types)]
    }
    
    return result