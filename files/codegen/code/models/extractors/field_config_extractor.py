"""Extract field configurations from TypeScript AST data."""


def generate_label(name: str) -> str:
    """Convert snake_case to Title Case"""
    return ' '.join(word.capitalize() for word in name.split('_'))


def get_field_type(name: str, type_text: str) -> str:
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
    
    # Get type to field mapping from loader
    loader = get_loader()
    type_to_field = loader.get_type_to_field_mapping()
    
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


def extract_field_configs(ast_data: dict) -> dict:
    """Extract field configurations from TypeScript AST data"""
    interfaces = ast_data.get('interfaces', [])
    enums = ast_data.get('enums', [])
    
    loader = get_loader()
    node_interface_map = loader.get_node_interface_map()
    base_fields = loader.get_base_fields()
    
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
                'type': get_field_type(name, type_text),
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


def main(inputs: dict) -> dict:
    """Main entry point for the field config extractor"""
    ast_data = inputs.get('default', {})
    return extract_field_configs(ast_data)