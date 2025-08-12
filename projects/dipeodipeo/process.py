"""Process generated DiPeO diagrams to clean up and format the output."""
import yaml
from typing import Any, Dict


def process_diagram(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a generated diagram to remove nulls and reorder keys.
    
    Args:
        inputs: Dictionary containing the generated diagram
        
    Returns:
        Dictionary with the processed diagram
    """
    
    def remove_nulls(obj):
        """Recursively remove null values from dictionaries and lists"""
        if isinstance(obj, dict):
            return {k: remove_nulls(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [remove_nulls(item) for item in obj if item is not None]
        else:
            return obj
    
    def order_diagram_keys(diagram):
        """Reorder diagram keys with 'version' first"""
        if not isinstance(diagram, dict):
            return diagram
        
        # Define the preferred key order
        key_order = ['version', 'name', 'description', 'persons', 'nodes', 'connections']
        
        # Create new ordered dict
        ordered = {}
        
        # Add keys in preferred order if they exist
        for key in key_order:
            if key in diagram:
                ordered[key] = diagram[key]
        
        # Add any remaining keys not in our preferred order
        for key in diagram:
            if key not in ordered:
                ordered[key] = diagram[key]
        
        return ordered
    
    def fix_newlines_in_code(diagram):
        """Convert escaped newlines to actual newlines in code fields"""
        if 'nodes' in diagram:
            for node in diagram['nodes']:
                if 'props' in node and isinstance(node['props'], dict):
                    if 'code' in node['props'] and isinstance(node['props']['code'], str):
                        # Replace escaped newlines with actual newlines
                        node['props']['code'] = node['props']['code'].replace('\n', '\n')
        return diagram

    # Extract the complete diagram YAML string from response
    generated_diagram = inputs.get('generated_diagram', {})
    diagram_yaml_string = generated_diagram['output'][1]['content'][0]['text']
    
    # Parse the YAML string to extract metadata
    diagram_dict = yaml.safe_load(diagram_yaml_string)
    
    # Get the diagram
    diagram = diagram_dict['diagram']
    
    # Remove null values
    diagram = remove_nulls(diagram)
    
    # Convert escaped newlines to actual newlines in code fields
    diagram = fix_newlines_in_code(diagram)
    
    # Reorder keys with 'version' at the top
    diagram = order_diagram_keys(diagram)
    
    return diagram