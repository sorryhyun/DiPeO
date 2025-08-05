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
    
    for filename, ast_data in inputs.items():
        if filename == 'default':
            # Skip the default key if present
            continue
            
        # Extract node type from filename (e.g., "api_job.data.ts.json" -> "api_job")
        if '.data.ts.json' in filename:
            node_type = filename.replace('.data.ts.json', '')
            
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
                    'properties': interface.get('properties', [])
                }
                print(f"Found data interface for {node_type}: {interface_name}")
    
    print(f"Extracted data for {len(node_data_by_type)} node types")
    
    return {'node_data': node_data_by_type}