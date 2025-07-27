"""Extract static node data from TypeScript AST."""

from datetime import datetime
from typing import Dict, List, Any, Optional


def get_python_type(ts_type: str, is_optional: bool, ts_to_py_type: dict) -> str:
    """Convert TypeScript type to Python type"""
    # Clean type
    clean_type = ts_type.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Handle string literal unions
    if ("'" in clean_type or '"' in clean_type) and '|' in clean_type:
        literals = []
        for lit in clean_type.split('|'):
            cleaned = lit.strip().replace("'", '').replace('"', '')
            literals.append(f'"{cleaned}"')
        literal_type = f"Literal[{', '.join(literals)}]"
        return f"Optional[{literal_type}]" if is_optional else literal_type
    
    # Check mapping first
    if clean_type in ts_to_py_type:
        mapped_type = ts_to_py_type[clean_type]
        # Handle optional wrapping for mapped types
        if is_optional and not mapped_type.startswith('Optional['):
            return f"Optional[{mapped_type}]"
        return mapped_type
    
    # Basic TypeScript to Python type mappings
    basic_type_map = {
        'string': 'str',
        'number': 'int',  # Default to int, not float
        'boolean': 'bool',
        'any': 'Any',
        'object': 'Dict[str, Any]',
        'null': 'None',
        'undefined': 'None',
        'void': 'None'
    }
    
    # Check basic type mappings
    if clean_type in basic_type_map:
        py_type = basic_type_map[clean_type]
        return f"Optional[{py_type}]" if is_optional and py_type != 'None' else py_type
    
    # Handle arrays
    if clean_type.endswith('[]'):
        inner_type = clean_type[:-2]
        inner_py = get_python_type(inner_type, False, ts_to_py_type)
        list_type = f"List[{inner_py}]"
        return f"Optional[{list_type}]" if is_optional else list_type
    
    # Handle Record types
    if clean_type.startswith('Record<'):
        return 'Dict[str, Any]'
    
    # Handle object literal types (e.g., { field: type; ... })
    # Enhanced detection to handle multi-line object types with comments
    if clean_type.startswith('{'):
        # Check if it looks like an object type by looking for common patterns
        # This handles both single-line and multi-line object definitions
        if (':' in clean_type or '?' in clean_type or ';' in clean_type or 
            '//' in clean_type or '/*' in clean_type):
            dict_type = 'Dict[str, Any]'
            return f"Optional[{dict_type}]" if is_optional else dict_type
    
    # If nothing matched, return the original type (might be a custom type)
    # Handle optional wrapping
    if is_optional and not clean_type.startswith('Optional['):
        return f"Optional[{clean_type}]"
    
    return clean_type


def extract_static_nodes_data(ast_data: dict, mappings: dict) -> dict:
    """Extract static node data from TypeScript AST"""
    interfaces = ast_data.get('interfaces', [])
    enums = ast_data.get('enums', [])
    
    # Get mappings
    node_interface_map = mappings.get('node_interface_map', {})
    base_fields = mappings.get('base_fields', ['label', 'flipped'])
    ts_to_py_type = mappings.get('ts_to_py_type', {})
    field_special_handling = mappings.get('field_special_handling', {})
    
    # Generate node classes data
    node_classes = []
    
    for node_type, interface_name in node_interface_map.items():
        # Skip PersonBatchJobNode as it's just an alias for PersonJobNode
        if node_type == 'person_batch_job':
            continue
            
        # Find interface
        interface_data = None
        for iface in interfaces:
            if iface.get('name') == interface_name:
                interface_data = iface
                break
        
        if not interface_data:
            continue
        
        class_name = interface_name.replace('NodeData', 'Node')
        
        # Get special handling for this node type
        node_special = field_special_handling.get(node_type, {})
        
        # Process fields
        fields = []
        for prop in interface_data.get('properties', []):
            ts_name = prop.get('name')
            
            # Skip base fields
            if ts_name in base_fields:
                continue
            
            # Get special handling for this field
            field_special = node_special.get(ts_name, {})
            
            # Determine Python name
            py_name = field_special.get('py_name', ts_name)
            
            ts_type = prop.get('type', 'Any')
            is_optional = prop.get('optional', False)
            py_type = get_python_type(ts_type, is_optional, ts_to_py_type)
            
            field_data = {
                'ts_name': ts_name,
                'py_name': py_name,
                'py_type': py_type,
                'has_default': False,
                'default_value': None,
                'is_field_default': False,
                'special_handling': field_special.get('special')
            }
            
            # Handle default values
            if 'default' in field_special:
                field_data['has_default'] = True
                field_data['default_value'] = field_special['default']
                field_data['is_field_default'] = 'field(' in field_special['default']
            elif is_optional:
                field_data['has_default'] = True
                field_data['default_value'] = 'None'
            elif not is_optional and 'Dict[' in py_type and 'Optional[' not in py_type:
                field_data['has_default'] = True
                field_data['default_value'] = 'field(default_factory=dict)'
                field_data['is_field_default'] = True
            elif not is_optional and 'List[' in py_type and 'Optional[' not in py_type:
                field_data['has_default'] = True
                field_data['default_value'] = 'field(default_factory=list)'
                field_data['is_field_default'] = True
            
            fields.append(field_data)
        
        node_classes.append({
            'class_name': class_name,
            'node_type': node_type,
            'fields': fields
        })
    
    return {
        'node_classes': node_classes,
        'now': datetime.now().isoformat()
    }


def main(inputs: dict) -> dict:
    """Main entry point for static nodes extraction"""
    ast_data = inputs.get('default', {})
    mappings = inputs.get('mappings', {})
    return extract_static_nodes_data(ast_data, mappings)