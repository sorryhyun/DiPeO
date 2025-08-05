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
    
    # Debug: Print all input keys
    print(f"Input keys: {list(inputs.keys())}")
    
    # Handle case where db node passes data as 'default'
    if 'default' in inputs and len(inputs) == 1:
        inputs = inputs['default']
        print(f"Unwrapped default key, new keys: {list(inputs.keys())}")
    
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
                            if const.get('name', '').endswith('Spec'):
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
            print(f"Found {len(node_specs)} specs from consolidated cache")
            return {'node_specs': node_specs}
        except Exception as e:
            print(f"Error reading consolidated cache: {e}")
    
    # Process individual spec files
    for filename, ast_data in inputs.items():
        if filename == 'default' or not filename.endswith('.spec.ts.json'):
            continue
        
        try:
            # Parse the AST data if it's a string
            if isinstance(ast_data, str):
                ast_data = json.loads(ast_data)
            
            # Extract the node specification
            for const in ast_data.get('constants', []):
                if const.get('name', '').endswith('Spec'):
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
                        print(f"Found spec for {node_type} in {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    print(f"Found {len(node_specs)} specs total")
    
    return {'node_specs': node_specs}