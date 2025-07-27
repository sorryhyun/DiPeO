"""TypeScript type mapping utilities."""
from typing import Dict, Any, List, Optional


def map_to_typescript_type(field_type: str, type_to_field: Optional[Dict[str, str]] = None) -> str:
    """Map generic field types to TypeScript types.
    
    Args:
        field_type: The field type to map
        type_to_field: Optional mapping from extracted codegen-mappings.ts
    """
    # First check if we have a UI field type mapping (for form fields)
    if type_to_field and field_type in type_to_field:
        # This is for UI field types, not TypeScript types
        # So we still need to map to actual TypeScript types
        pass
    
    # Basic type mappings for TypeScript
    type_map = {
        'string': 'string',
        'str': 'string',
        'text': 'string',
        'int': 'number',
        'integer': 'number',
        'float': 'number',
        'number': 'number',
        'double': 'number',
        'bool': 'boolean',
        'boolean': 'boolean',
        'dict': 'Record<string, any>',
        'object': 'Record<string, any>',
        'list': 'any[]',
        'array': 'any[]',
        'any': 'any',
        'null': 'null',
        'undefined': 'undefined',
        'void': 'void',
        'date': 'Date',
        'datetime': 'Date',
        'enum': 'string',  # Will be overridden if enum values provided
    }
    
    # Handle array types like string[], number[]
    if field_type.endswith('[]'):
        base_type = field_type[:-2]
        mapped_base = map_to_typescript_type(base_type, type_to_field)
        return f"{mapped_base}[]"
    
    # Handle generic types like Array<string>, List<number>
    if '<' in field_type and '>' in field_type:
        base_type = field_type.split('<')[0].lower()
        inner_type = field_type.split('<')[1].rstrip('>')
        
        if base_type in ['array', 'list']:
            return f"{map_to_typescript_type(inner_type, type_to_field)}[]"
        elif base_type in ['dict', 'map', 'record']:
            if ',' in inner_type:
                key_type, value_type = inner_type.split(',', 1)
                return f"Record<{map_to_typescript_type(key_type.strip(), type_to_field)}, {map_to_typescript_type(value_type.strip(), type_to_field)}>"
            else:
                return f"Map<string, {map_to_typescript_type(inner_type, type_to_field)}>"
    
    return type_map.get(field_type.lower(), field_type)


def get_typescript_default(field: Dict[str, Any]) -> str:
    """Get TypeScript default value for a field."""
    if 'default' in field:
        default = field['default']
        field_type = field.get('type', 'string')
        
        # Handle different default types
        if isinstance(default, str):
            return f"'{default}'"
        elif isinstance(default, bool):
            return 'true' if default else 'false'
        elif isinstance(default, (int, float)):
            return str(default)
        elif isinstance(default, list):
            return '[]'
        elif isinstance(default, dict):
            return '{}'
        elif default is None:
            return 'undefined'
    
    # Return type-based defaults
    field_type = field.get('type', 'string')
    ts_type = map_to_typescript_type(field_type)
    
    if ts_type == 'string':
        return "''"
    elif ts_type == 'number':
        return '0'
    elif ts_type == 'boolean':
        return 'false'
    elif ts_type.endswith('[]'):
        return '[]'
    elif ts_type.startswith('Record<'):
        return '{}'
    else:
        return 'undefined'


def get_zod_schema(field: Dict[str, Any], type_to_zod: Optional[Dict[str, str]] = None) -> str:
    """Generate Zod schema for a field.
    
    Args:
        field: Field definition
        type_to_zod: Optional mapping from extracted codegen-mappings.ts
    """
    field_type = field.get('type', 'string')
    
    # Check centralized mappings first
    if type_to_zod and field_type in type_to_zod:
        schema = type_to_zod[field_type]
    else:
        # Fall back to generating schema based on TypeScript type
        ts_type = map_to_typescript_type(field_type)
        
        # Base schema
        if ts_type == 'string':
            schema = 'z.string()'
        elif ts_type == 'number':
            schema = 'z.number()'
        elif ts_type == 'boolean':
            schema = 'z.boolean()'
        elif ts_type.endswith('[]'):
            inner_type = ts_type[:-2]
            if inner_type == 'string':
                schema = 'z.array(z.string())'
            elif inner_type == 'number':
                schema = 'z.array(z.number())'
            else:
                schema = 'z.array(z.any())'
        elif ts_type.startswith('Record<'):
            schema = 'z.record(z.any())'
        else:
            schema = 'z.any()'
    
    # Add validations
    if field.get('required', False):
        pass  # Required by default in zod
    else:
        schema += '.optional()'
    
    # Check for validation constraints - can be direct on field or in validation object
    validation = field.get('validation', {})
    
    # Min constraint
    min_val = field.get('min') or validation.get('min')
    if min_val is not None:
        field_ts_type = map_to_typescript_type(field_type)
        if field_ts_type == 'string':
            schema += f'.min({min_val})'
        elif field_ts_type == 'number':
            schema += f'.min({min_val})'
    
    # Max constraint
    max_val = field.get('max') or validation.get('max')
    if max_val is not None:
        field_ts_type = map_to_typescript_type(field_type)
        if field_ts_type == 'string':
            schema += f'.max({max_val})'
        elif field_ts_type == 'number':
            schema += f'.max({max_val})'
    
    # Pattern constraint
    pattern = field.get('pattern') or validation.get('pattern')
    if pattern:
        # Escape forward slashes in the pattern for JavaScript regex literal
        escaped_pattern = pattern.replace('/', '\\/')
        schema += f'.regex(/{escaped_pattern}/)'
    
    if 'default' in field:
        default_value = get_typescript_default(field)
        schema += f'.default({default_value})'
    
    return schema


def calculate_typescript_imports(spec_data: Dict[str, Any]) -> List[str]:
    """Calculate TypeScript imports needed for the model."""
    imports = []
    has_zod = False
    
    # Check if we need zod
    for field in spec_data.get('fields', []):
        if field.get('validation') or field.get('required'):
            has_zod = True
            break
    
    if has_zod:
        imports.append("import { z } from 'zod';")
    
    # Base imports
    imports.append("import { BaseNode } from '../base';")
    
    # Check for special types that need imports
    field_types = set()
    for field in spec_data.get('fields', []):
        field_type = field.get('type', 'string')
        field_types.add(field_type)
    
    # Add any additional imports based on field types
    if 'date' in field_types or 'datetime' in field_types:
        imports.append("import { parseISO } from 'date-fns';")
    
    return imports