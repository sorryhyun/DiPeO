"""Save AST result from typescript_ast node to temp file."""

import json
import os
from pathlib import Path
from typing import Dict, Any


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save the parsed AST result to a temporary file.
    
    Args:
        inputs: Dictionary containing:
            - default: AST parsing result from typescript_ast node
            - node_info: Metadata about the node being parsed
    
    Returns:
        Dictionary containing the parsed interface data.
    """
    # Get AST result from typescript_ast node
    ast_result = inputs.get('ast_data')
    if not ast_result:
        # Try default if ast_data not found
        ast_result = inputs.get('default', {})
    
    node_info = inputs.get('node_info', {})
    
    # Extract node type from node_info
    node_type = node_info.get('node_type', 'unknown')
    cache_filename = node_info.get('cache_filename', node_type)
    
    # Ensure .temp directory exists
    temp_dir = Path('.temp')
    temp_dir.mkdir(exist_ok=True)
    
    # Save AST result to cache file
    cache_path = temp_dir / f"{cache_filename}_ast.json"
    with open(cache_path, 'w') as f:
        json.dump(ast_result, f, indent=2)
    
    print(f"[Save AST Result] Saved {node_type} AST to {cache_path}")
    
    # Extract the main interface from the result
    interfaces = ast_result.get('interfaces', [])
    if interfaces:
        # Find the main interface (usually has the same name as the node)
        main_interface = None
        for interface in interfaces:
            if interface.get('name', '').lower().replace('nodedata', '') == node_type.replace('_', ''):
                main_interface = interface
                break
        
        if not main_interface and interfaces:
            # Fallback to first interface if exact match not found
            main_interface = interfaces[0]
        
        return {
            'parsed_node': {
                'node_type': node_type,
                'interface': main_interface,
                'all_interfaces': interfaces,
                'types': ast_result.get('types', []),
                'enums': ast_result.get('enums', []),
                'total_definitions': ast_result.get('total_definitions', 0)
            }
        }
    
    return {
        'parsed_node': {
            'node_type': node_type,
            'interface': None,
            'all_interfaces': [],
            'types': ast_result.get('types', []),
            'enums': ast_result.get('enums', []),
            'total_definitions': ast_result.get('total_definitions', 0)
        }
    }