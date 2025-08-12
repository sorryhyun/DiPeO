"""Process generated DiPeO diagrams to clean up and format the output."""
import yaml
from typing import Any, Dict
from io import StringIO


# Custom YAML representer for better multiline string formatting
class LiteralScalarString(str):
    """A string that should be represented as a literal block scalar in YAML."""
    pass


def literal_scalar_representer(dumper, data):
    """Represent a string as a literal block scalar (|) in YAML."""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')


def process_diagram(inputs: Dict[str, Any]) -> str:
    """
    Process a generated diagram to remove nulls, reorder keys, and format as YAML.
    
    Args:
        inputs: Dictionary containing the generated diagram
        
    Returns:
        String with the formatted YAML output
    """
    
    def remove_nulls_and_empty(obj):
        """Recursively remove null values and empty collections from dictionaries and lists"""
        if isinstance(obj, dict):
            cleaned = {}
            for k, v in obj.items():
                # Skip empty persons field
                if k == 'persons' and (v is None or (isinstance(v, dict) and not v)):
                    continue
                cleaned_value = remove_nulls_and_empty(v)
                if cleaned_value is not None:
                    cleaned[k] = cleaned_value
            return cleaned if cleaned else None
        elif isinstance(obj, list):
            cleaned = [remove_nulls_and_empty(item) for item in obj if item is not None]
            return cleaned if cleaned else None
        else:
            return obj
    
    def fix_code_fields(diagram):
        """Convert code fields to use literal scalar format for better readability"""
        if 'nodes' in diagram:
            for node in diagram['nodes']:
                if 'props' in node and isinstance(node['props'], dict):
                    if 'code' in node['props'] and isinstance(node['props']['code'], str):
                        # Replace escaped newlines with actual newlines
                        code = node['props']['code'].replace('\\n', '\n')
                        # Ensure code ends with newline to get | instead of |-
                        if not code.endswith('\n'):
                            code += '\n'
                        # Mark as literal scalar string for YAML formatting
                        node['props']['code'] = LiteralScalarString(code)
        return diagram

    # Extract the complete diagram YAML string from response
    generated_diagram = inputs.get('generated_diagram', {})
    diagram_yaml_string = generated_diagram['output'][1]['content'][0]['text']
    
    # Parse the YAML string to extract metadata
    diagram_dict = yaml.safe_load(diagram_yaml_string)
    
    # Get the diagram
    diagram = diagram_dict['diagram']
    
    # Remove null values and empty persons
    diagram = remove_nulls_and_empty(diagram)
    
    # Fix code fields for proper multiline formatting
    diagram = fix_code_fields(diagram)
    
    # Create custom YAML dumper
    yaml_dumper = yaml.SafeDumper
    yaml_dumper.add_representer(LiteralScalarString, literal_scalar_representer)
    
    # Define the preferred key order
    key_order = ['version', 'name', 'description', 'persons', 'nodes', 'connections']
    
    # Create ordered diagram with version first
    ordered_diagram = {}
    for key in key_order:
        if key in diagram:
            ordered_diagram[key] = diagram[key]
    
    # Add any remaining keys not in our preferred order
    for key in diagram:
        if key not in ordered_diagram:
            ordered_diagram[key] = diagram[key]
    
    # Generate YAML string with proper formatting
    stream = StringIO()
    yaml.dump(ordered_diagram, stream, 
              Dumper=yaml_dumper,
              default_flow_style=False, 
              sort_keys=False,  # Preserve our key order
              allow_unicode=True,
              width=120)  # Wider lines for better code formatting
    
    return stream.getvalue()