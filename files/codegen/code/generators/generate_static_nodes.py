"""Generate static nodes from parsed TypeScript data."""
import json
from datetime import datetime
from typing import Any, Dict, List

# Import the static nodes extractor
from files.codegen.code.models.extractors.static_nodes_extractor import extract_static_nodes_data


def generate_static_nodes(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate static nodes from all parsed TypeScript data.
    
    Args:
        inputs: Dictionary containing mappings, temp_results, and base_data
        
    Returns:
        Dictionary with extracted static node data
    """
    # Get inputs
    mappings = inputs.get('mappings', {})
    temp_results = inputs.get('temp_results', {})
    base_data = inputs.get('base_data', {})
    
    # Extract base interface
    base_interface = base_data.get('base_interface')
    
    # Get parsed nodes from temp results
    parsed_nodes = temp_results.get('parsed_nodes', [])
    
    # Combine all interfaces
    all_interfaces: List[Dict[str, Any]] = []
    node_interface_map = mappings.get('node_interface_map', {})
    
    for parsed in parsed_nodes:
        node_type = parsed.get('node_type')
        interface_name = parsed.get('interface_name')
        interface_data = parsed.get('interface')
        
        if interface_data:
            # Update the node_interface_map with actual names
            node_interface_map[node_type] = interface_name
            all_interfaces.append(interface_data)
    
    if not all_interfaces:
        raise ValueError("No interfaces were successfully parsed from node data files")
    
    # Update mappings with the collected interface names
    mappings['node_interface_map'] = node_interface_map
    
    # Create combined AST data
    combined_ast = {
        'interfaces': all_interfaces,
        'base_interface': base_interface
    }
    
    # Run the static nodes extractor
    result = extract_static_nodes_data(combined_ast, mappings)
    
    return result