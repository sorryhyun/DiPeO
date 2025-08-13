"""Extract node specifications from dynamically loaded AST files."""
import json
from typing import Any, Dict, List


def extract_node_specs_from_ast(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node specifications from all loaded spec AST files.
    
    Args:
        inputs: Dictionary containing loaded AST data from glob pattern
        
    Returns:
        Dictionary with extracted node specifications
    """
    
    node_specs = []
    
    # Handle CodeJobNode's input wrapping structure
    # CodeJobNode adds 'inputs' and 'node_id' keys
    if 'inputs' in inputs and 'node_id' in inputs:
        # Get the actual data from the inputs wrapper
        actual_inputs = inputs.get('inputs', {})
        
        # The DB node output is typically in 'default' key
        if 'default' in actual_inputs:
            inputs = actual_inputs['default']
    # Handle simple case where db node passes data as 'default'
    elif 'default' in inputs and len(inputs) == 1:
        inputs = inputs['default']

    # Check for consolidated cache file in inputs
    if 'all_node_specs_ast.json' in inputs:
        try:
            data = inputs['all_node_specs_ast.json']
            if isinstance(data, str):
                data = json.loads(data)
            
            # The structure is: { "node_specs": { "node_name": { "constants": [...] } } }
            if 'node_specs' in data:
                for node_name, node_data in data['node_specs'].items():
                    if isinstance(node_data, dict) and 'constants' in node_data:
                        for const in node_data['constants']:
                            # Check for both 'Spec' and 'spec' to handle camelCase naming
                            name = const.get('name', '')
                            if name.endswith('Spec') or name.endswith('spec'):
                                spec_value = const.get('value', {})
                                if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                                    # Clean up nodeType (remove quotes and NodeType. prefix)
                                    node_type = spec_value.get('nodeType', '')
                                    node_type = node_type.replace('NodeType.', '').replace('"', '').lower()
                                    
                                    node_specs.append({
                                        'name': node_type,
                                        'displayName': spec_value.get('displayName'),
                                        'category': spec_value.get('category'),
                                        'description': spec_value.get('description'),
                                        'fields': spec_value.get('fields', [])
                                    })
            return {'node_specs': node_specs}
        except Exception as e:
            pass
            # print(f"Error reading consolidated cache: {e}")
    
    # Process individual spec files
    for filename, ast_data in inputs.items():
        # Skip special keys
        if filename == 'default':
            continue
        
        # Check if this is a spec file (handle both filename and full path)
        import os
        base_filename = os.path.basename(filename)
        if not base_filename.endswith('.spec.ts.json'):
            continue
        
        try:
            # Parse the AST data if it's a string
            if isinstance(ast_data, str):
                ast_data = json.loads(ast_data)
            
            # Extract the node specification
            for const in ast_data.get('constants', []):
                # Check for both 'Spec' and 'spec' to handle camelCase naming
                name = const.get('name', '')
                if name.endswith('Spec') or name.endswith('spec'):
                    spec_value = const.get('value', {})
                    if isinstance(spec_value, dict) and 'nodeType' in spec_value:
                        # Clean up nodeType (remove quotes and NodeType. prefix)
                        node_type = spec_value.get('nodeType', '')
                        node_type = node_type.replace('NodeType.', '').replace('"', '').lower()
                        
                        node_specs.append({
                            'name': node_type,
                            'displayName': spec_value.get('displayName'),
                            'category': spec_value.get('category'),
                            'description': spec_value.get('description'),
                            'fields': spec_value.get('fields', [])
                        })
        except Exception as e:
            pass
            # Silently continue on error

    return {'node_specs': node_specs}