"""
Field configurations generator for DiPeO nodes.
Consolidates all field config generation logic into a single module.
"""

import os
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from jinja2 import Template, StrictUndefined


# ============================================================================
# Helper Functions
# ============================================================================

def extract_mappings_from_ast(mappings_ast: dict) -> dict:
    """Extract mappings from codegen mappings AST"""
    # This is a simplified version - in real implementation, you'd parse the AST properly
    return {
        'node_interface_map': {},
        'base_fields': ['label', 'flipped'],
        'type_to_field': {
            'string': 'text',
            'number': 'number',
            'boolean': 'checkbox'
        }
    }


# ============================================================================
# Field Config Extraction
# ============================================================================

def generate_label(name: str) -> str:
    """Convert snake_case to Title Case"""
    return ' '.join(word.capitalize() for word in name.split('_'))


def get_field_type(name: str, type_text: str, type_to_field: dict) -> str:
    """Determine the appropriate field type - must match FIELD_TYPES from panel.ts"""
    # Special handling for specific field names
    if any(keyword in name for keyword in ['prompt', 'expression', 'query']):
        return 'variableTextArea'
    
    if name == 'code' or name == 'script':
        return 'code'
    
    if name == 'url':
        return 'url'
    
    if name == 'filePath' or name == 'file_path' or name == 'path':
        return 'filepath'
    
    if name == 'max_iteration':
        return 'maxIteration'
    
    if name == 'person':
        return 'personSelect'
    
    # Clean type text
    clean_type = type_text.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Check for branded types
    if 'PersonID' in clean_type:
        return 'personSelect'
    
    # Check mapping
    if clean_type in type_to_field:
        return type_to_field[clean_type]
    
    # Handle Record types - use code editor for better editing
    if 'Record<' in type_text:
        return 'code'
    
    # Handle arrays
    if '[]' in type_text:
        return 'textarea'
    
    # Handle object types
    if clean_type == 'object' or type_text.startswith('{'):
        return 'code'
    
    return 'text'


def add_type_specific_props(field_config: dict, name: str, type_text: str, enum_values: dict) -> None:
    """Add type-specific properties to field config"""
    # Add placeholders
    if 'prompt' in name:
        field_config['placeholder'] = 'Enter prompt. Use {{variable_name}} for variables.'
        field_config['rows'] = 6
    elif name == 'code':
        field_config['placeholder'] = 'Enter code here'
        field_config['rows'] = 10
    elif name == 'url':
        field_config['placeholder'] = 'https://api.example.com/endpoint'
    elif name == 'timeout':
        field_config['placeholder'] = 'Timeout in seconds'
        field_config['min'] = 0
        field_config['max'] = 600
    
    # Add select options for enums
    clean_type = type_text.replace(' | null', '').replace(' | undefined', '').strip()
    if clean_type in enum_values:
        values = enum_values[clean_type]
        field_config['options'] = [
            {'value': val, 'label': generate_label(val)}
            for val in values
        ]
    
    # Add defaults
    if type_text == 'number':
        if name == 'max_iteration':
            field_config['defaultValue'] = 1
            field_config['min'] = 1
            field_config['max'] = 100
        elif name == 'timeout':
            field_config['defaultValue'] = 30
    elif type_text == 'boolean':
        field_config['defaultValue'] = False


def extract_enum_values(enums: list) -> dict:
    """Extract enum values from AST data"""
    enum_values = {}
    for enum in enums:
        name = enum.get('name', '')
        members = enum.get('members', [])
        values = []
        for member in members:
            # Extract the value, defaulting to member name if no explicit value
            value = member.get('value', member.get('name', ''))
            values.append(value)
        enum_values[name] = values
    return enum_values


def extract_field_configs_core(ast_data: dict, mappings: dict) -> dict:
    """Extract field configurations from TypeScript AST data"""
    interfaces = ast_data.get('interfaces', [])
    enums = ast_data.get('enums', [])
    
    # Get mappings
    node_interface_map = mappings.get('node_interface_map', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])
    type_to_field = mappings.get('type_to_field', {})
    
    # Build enum value map
    enum_values = extract_enum_values(enums)
    
    # Generate field configs for each node type
    node_configs = []
    
    for node_type, interface_name in node_interface_map.items():
        # Find the interface
        interface_data = None
        for iface in interfaces:
            if iface.get('name') == interface_name:
                interface_data = iface
                break
        
        if not interface_data:
            print(f"Warning: Interface {interface_name} not found")
            continue
        
        # Extract fields
        fields = []
        for prop in interface_data.get('properties', []):
            name = prop.get('name', '')
            
            # Skip base fields
            if name in base_fields:
                continue
            
            type_text = prop.get('type', 'string')
            is_optional = prop.get('optional', False)
            
            field_config = {
                'name': name,
                'type': get_field_type(name, type_text, type_to_field),
                'label': generate_label(name),
                'required': not is_optional
            }
            
            # Add type-specific properties
            add_type_specific_props(field_config, name, type_text, enum_values)
            
            fields.append(field_config)
        
        node_configs.append({
            'nodeType': node_type,
            'fields': fields
        })
    
    print(f"Generated field configs for {len(node_configs)} node types")
    
    return {
        'node_configs': node_configs,
        'enum_values': enum_values
    }


# ============================================================================
# Main Functions (called by diagram nodes)
# ============================================================================

def extract_field_configs(inputs: dict) -> dict:
    """Main entry point for the field config extractor"""
    # Check if we have the new format (single input with multiple files)
    if 'ast_files' in inputs and isinstance(inputs['ast_files'], dict):
        # New format: dictionary where keys are file paths and values are file contents
        file_dict = inputs['ast_files']
        
        # Parse AST data from the files
        diagram_ast = None
        node_data_ast = None
        mappings_ast = None
        
        for filepath, content in file_dict.items():
            if filepath.endswith('diagram_ast.json'):
                diagram_ast = content if isinstance(content, dict) else json.loads(content)
            elif filepath.endswith('node_data_ast.json'):
                node_data_ast = content if isinstance(content, dict) else json.loads(content)
            elif filepath.endswith('codegen_mappings_ast.json'):
                mappings_ast = content if isinstance(content, dict) else json.loads(content)
        
        # Get mappings
        mappings = inputs.get('mappings', {})
        if not mappings and mappings_ast:
            # Extract mappings from AST if not provided separately
            mappings = extract_mappings_from_ast(mappings_ast)
    else:
        # Legacy format: separate inputs
        node_data_ast = inputs.get('node_data', {})
        diagram_ast = inputs.get('default', {})
        mappings = inputs.get('mappings', {})
    
    # If node_data is just the index file, we need to aggregate from individual files
    if not node_data_ast or not node_data_ast.get('interfaces'):
        # Load individual node data files
        base_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))
        cache_dir = base_dir / '.temp'
        all_interfaces = []
        
        print(f"Loading individual node data files from {cache_dir}")
        
        # Pattern to match individual node data files
        matching_files = list(cache_dir.glob('*_data_ast.json'))
        print(f"Found {len(matching_files)} matching files")
        
        for ast_file in matching_files:
            # Skip the index file
            if ast_file.name == 'node_data_ast.json':
                continue
            
            try:
                with open(ast_file, 'r') as f:
                    data = json.load(f)
                    interfaces = data.get('interfaces', [])
                    all_interfaces.extend(interfaces)
                    if interfaces:
                        print(f"  Loaded {ast_file.name}: {len(interfaces)} interfaces")
            except Exception as e:
                print(f"Error loading {ast_file}: {e}")
        
        # Create aggregated AST data
        node_data_ast = {
            'interfaces': all_interfaces,
            'types': [],
            'enums': [],
            'constants': []
        }
        
        print(f"Total interfaces in aggregated data: {len(all_interfaces)}")
    
    mappings = inputs.get('mappings', {})
    return extract_field_configs_core(node_data_ast, mappings)


def prepare_template_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare field configuration data for template rendering."""
    # Get the extracted field configs - it returns a dict with 'node_configs' key
    field_configs_data = inputs.get('node_configs', {})
    
    # Extract the actual node configs array
    if isinstance(field_configs_data, dict):
        node_configs = field_configs_data.get('node_configs', [])
    else:
        node_configs = field_configs_data
    
    print(f"Preparing template data with {len(node_configs)} node configs")
    if node_configs:
        print(f"First node config keys: {list(node_configs[0].keys()) if node_configs else []}")
    
    result = {
        'node_configs': node_configs,
        'now': datetime.now().isoformat()
    }
    
    return result


def render_field_configs(inputs: Dict[str, Any]) -> str:
    """Render field configurations using Jinja2 template."""
    # Get template content
    template_content = inputs.get('template_content', '')
    
    # Get prepared data
    template_data = inputs.get('default', {})
    
    print(f"Template data keys: {list(template_data.keys())}")
    print(f"Node configs count: {len(template_data.get('node_configs', []))}")
    
    try:
        # Render template
        jinja_template = Template(template_content, undefined=StrictUndefined)
        rendered = jinja_template.render(**template_data)
        
        print(f"Successfully rendered template, length: {len(rendered)}")
        
        # DB write node expects the string directly as 'default' input
        return rendered
    except Exception as e:
        print(f"Template rendering error: {e}")
        print(traceback.format_exc())
        # Return error as content so we can see it
        return f"/* Template rendering error: {e} */\n"


# Backward compatibility aliases
main = extract_field_configs
prepare_field_config_data = prepare_template_data