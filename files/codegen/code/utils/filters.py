"""
Filter functions for Jinja2 templates in code generation.
"""

import json
import re
from typing import Dict, Any
from .type_converters import to_zod_type


def typescript_type_filter(field: Dict[str, Any]) -> str:
    """Convert field to TypeScript type."""
    type_map = {
        'string': 'string',
        'number': 'number',
        'boolean': 'boolean',
        'select': 'string',
        'multiselect': 'string[]',
        'json': 'any',
        'array': 'any[]',
        'object': 'Record<string, any>'
    }
    return type_map.get(field.get('type', 'string'), 'any')


def python_type_filter(field: Dict[str, Any]) -> str:
    """Convert field to Python type hint."""
    type_map = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'select': 'str',
        'multiselect': 'List[str]',
        'json': 'Dict[str, Any]',
        'array': 'List[Any]',
        'object': 'Dict[str, Any]'
    }
    
    py_type = type_map.get(field.get('type', 'string'), 'Any')
    
    # Handle arrays
    if field.get('array', False) and not py_type.startswith('List'):
        py_type = f'List[{py_type}]'
    
    # Handle optional
    if not field.get('required', False):
        py_type = f'Optional[{py_type}]'
    
    return py_type


def python_default_filter(field: Dict[str, Any]) -> str:
    """Generate Python default value based on field type."""
    if 'default' in field:
        default = field['default']
        if isinstance(default, str):
            return f'"{default}"'
        elif isinstance(default, bool):
            return str(default)
        else:
            return json.dumps(default)
    
    # Return None for optional fields
    if not field.get('required', False):
        return 'None'
    
    # No default for required fields
    return ''


def graphql_type_filter(field: Dict[str, Any]) -> str:
    """Convert field to GraphQL type."""
    base_type = field.get('type', 'string')
    is_array = field.get('array', False)
    
    type_map = {
        'string': 'String',
        'number': 'Float',
        'boolean': 'Boolean',
        'select': 'String',
        'multiselect': '[String!]',
        'json': 'JSON',
        'array': '[JSON!]',
        'object': 'JSON'
    }
    
    graphql_type = type_map.get(base_type, 'String')
    
    # Handle arrays
    if is_array and not graphql_type.startswith('['):
        graphql_type = f'[{graphql_type}!]'
    
    return graphql_type


def zod_schema_filter(field: Dict[str, Any]) -> str:
    """Convert field to Zod schema."""
    # Use the utility function for base type conversion
    base_schema = to_zod_type(field)
    
    # Add optional if not required
    if not field.get('required', False):
        base_schema += ".optional()"
    
    # Add default if provided
    if 'default' in field:
        default_val = field['default']
        if isinstance(default_val, str):
            base_schema += f'.default("{default_val}")'
        else:
            base_schema += f'.default({json.dumps(default_val)})'
    
    return base_schema


def default_value_filter(field: Dict[str, Any]) -> str:
    """Generate default value based on field type."""
    if 'default' in field:
        default = field['default']
        if isinstance(default, str):
            return f'"{default}"'
        elif isinstance(default, bool):
            return str(default).lower()
        else:
            return json.dumps(default)
    
    # Generate default based on type
    type_defaults = {
        'string': '""',
        'number': '0',
        'boolean': 'false',
        'select': '""',
        'multiselect': '[]',
        'json': '{}',
        'array': '[]',
        'object': '{}'
    }
    
    return type_defaults.get(field.get('type', 'string'), 'null')


def humanize_filter(text: str) -> str:
    """Convert snake_case or camelCase to human readable format."""
    # Handle snake_case
    if '_' in text:
        return ' '.join(word.capitalize() for word in text.split('_'))
    
    # Handle camelCase
    result = re.sub('([a-z])([A-Z])', r'\\1 \\2', str(text))
    return result[0].upper() + result[1:] if result else ''


def ui_field_type_filter(field: Dict[str, Any]) -> str:
    """Determine the appropriate UI field type based on field configuration."""
    # First check if uiConfig explicitly specifies the inputType
    if field.get('uiConfig', {}).get('inputType'):
        return field['uiConfig']['inputType']
    
    # Otherwise, map from the base type
    field_type = field.get('type', 'string')
    field_name = field.get('name', '').lower()
    
    # Check for special cases
    if field_type == 'string':
        # URL detection
        if 'url' in field_name or field_name.endswith('_url') or field_name.endswith('endpoint'):
            return 'url'
        
        # File path detection
        if 'path' in field_name or field_name.endswith('_path') or 'file' in field_name:
            return 'filepath'
        
        # Code/query detection
        if any(keyword in field_name for keyword in ['query', 'template', 'script', 'code', 'sql', 'graphql']):
            return 'code'
        
        # Password detection
        if any(keyword in field_name for keyword in ['password', 'secret', 'token', 'api_key']):
            return 'password'
        
        # Check if it should be a textarea based on name or other hints
        if any(hint in field_name for hint in ['prompt', 'description', 'content', 'text', 'message', 'body']):
            return 'textarea'
        
        return 'text'
    elif field_type == 'enum' or field_type == 'select':
        return 'select'
    elif field_type == 'boolean':
        return 'checkbox'
    elif field_type == 'number':
        return 'number'
    elif field_type == 'array':
        # Check if it's a multi-select
        if field.get('uiConfig', {}).get('multiSelect'):
            return 'multiselect'
        return 'custom'  # Arrays use custom field type
    elif field_type == 'object' or field_type == 'json':
        return 'textarea'  # JSON uses textarea for editing
    elif field_type == 'code':
        return 'code'
    else:
        return 'text'