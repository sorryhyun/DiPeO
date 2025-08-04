import json


def main(inputs):
    """Extract interface data from cached AST."""
    # Parse cached AST data - handle both dict and string inputs
    if isinstance(inputs, str):
        # If inputs is a string, it's likely the AST data directly
        ast_data = json.loads(inputs) if inputs else {}
        node_info = {}
        node_type = 'unknown'
    else:
        ast_data = inputs.get('ast_data', {})
        if isinstance(ast_data, str):
            ast_data = json.loads(ast_data)
        
        node_info = inputs.get('node_info', {})
        node_type = node_info.get('node_type', 'unknown')
    
    interfaces = ast_data.get('interfaces', [])
    types = ast_data.get('types', [])
    
    # Find the interface or type for this node type
    interface_name = None
    interface_data = None
    
    # First check interfaces
    for iface in interfaces:
        name = iface.get('name', '')
        # Match interface name pattern like PersonJobNodeData
        if name.endswith('NodeData'):
            interface_data = iface
            interface_name = name
            break
    
    # If not found in interfaces, check types
    if not interface_data:
        for type_def in types:
            name = type_def.get('name', '')
            if name.endswith('NodeData'):
                interface_data = type_def
                interface_name = name
                break
    
    if not interface_data:
        # If still not found, try to handle cases where data might be missing
        # Return a placeholder that won't break the parent process
        result = {
            'node_type': node_type,
            'interface_name': None,
            'interface': None,
            'error': f"No interface or type found for node type: {node_type}"
        }
    else:
        result = {
            'node_type': node_type,
            'interface_name': interface_name,
            'interface': interface_data
        }
    
    return result