"""Extract node data from dynamically loaded AST files."""
import json
from typing import Any, Dict, List


def extract_node_data_from_ast(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node data from all loaded AST files.
    
    Args:
        inputs: Dictionary containing loaded AST data from glob pattern
        
    Returns:
        Dictionary with extracted node data organized by node type
    """
    
    # The db node with glob returns a dict with filenames as keys
    node_data_by_type = {}
    
    print(f"[extract_node_data_from_ast] inputs keys: {list(inputs.keys())}")
    print(f"[extract_node_data_from_ast] inputs type: {type(inputs)}")
    
    # Handle wrapped inputs (runtime resolver may wrap in 'default')
    if 'default' in inputs and isinstance(inputs['default'], dict):
        actual_inputs = inputs['default']
    else:
        actual_inputs = inputs
    
    for filepath, ast_data in actual_inputs.items():
        if filepath == 'default':
            # Skip the default key if present
            continue
            
        # Extract filename from path
        filename = filepath.split('/')[-1] if '/' in filepath else filepath
        
        # Extract node type from filename (e.g., "api-job.data.ts.json" -> "api_job")
        if '.data.ts.json' in filename:
            # Replace hyphens with underscores for node_type
            node_type = filename.replace('.data.ts.json', '').replace('-', '_')
            
            # Parse the AST data if it's a string
            if isinstance(ast_data, str):
                ast_data = json.loads(ast_data)
            
            # Extract the data interface from the AST
            data_interface = None
            for interface in ast_data.get('interfaces', []):
                interface_name = interface.get('name', '')
                # Look for the data interface (e.g., ApiJobData, CodeJobData)
                if interface_name.endswith('Data') and not interface_name.startswith('Base'):
                    data_interface = interface
                    break
            
            if data_interface:
                node_data_by_type[node_type] = {
                    'interface': data_interface,
                    'properties': data_interface.get('properties', [])
                }
                print(f"Found data interface for {node_type}: {data_interface.get('name', '')}")
    
    print(f"Extracted data for {len(node_data_by_type)} node types")
    
    return {'node_data': node_data_by_type}