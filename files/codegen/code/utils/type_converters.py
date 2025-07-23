"""Type conversion utilities for code generation."""

from typing import Dict, Set


def to_zod_type(field_or_type) -> str:
    """Convert Python type to Zod schema type.
    
    Can accept either a string type or a field dictionary with 'type' key.
    """
    # Handle both string and dict inputs
    if isinstance(field_or_type, dict):
        python_type = field_or_type.get('type', 'Any')
        is_required = field_or_type.get('required', True)
    else:
        python_type = str(field_or_type)
        is_required = True
    
    # Basic type mappings
    type_map = {
        'str': 'z.string()',
        'int': 'z.number().int()',
        'float': 'z.number()',
        'bool': 'z.boolean()',
        'Any': 'z.any()',
        'None': 'z.null()',
        'datetime': 'z.date()',
        'date': 'z.date()',
    }
    
    # Check basic types
    if python_type in type_map:
        return type_map[python_type]
    
    # Handle Optional types
    if python_type.startswith('Optional[') and python_type.endswith(']'):
        inner_type = python_type[9:-1]
        inner_zod = to_zod_type(inner_type)
        return f'{inner_zod}.optional()'
    
    # Handle List types
    if python_type.startswith('List[') and python_type.endswith(']'):
        inner_type = python_type[5:-1]
        inner_zod = to_zod_type(inner_type)
        return f'z.array({inner_zod})'
    
    # Handle Dict types
    if python_type.startswith('Dict[') and python_type.endswith(']'):
        # For simplicity, assume string keys
        parts = python_type[5:-1].split(', ', 1)
        if len(parts) == 2:
            value_zod = to_zod_type(parts[1])
            return f'z.record(z.string(), {value_zod})'
    
    # Handle Union types
    if python_type.startswith('Union[') and python_type.endswith(']'):
        parts = python_type[6:-1].split(', ')
        zod_parts = [to_zod_type(p.strip()) for p in parts]
        return f'z.union([{", ".join(zod_parts)}])'
    
    # Handle Literal types
    if python_type.startswith('Literal[') and python_type.endswith(']'):
        return f'z.literal({python_type[8:-1]})'
    
    # Default: assume it's a custom type/schema
    return f'{python_type}Schema'


def to_zod_schema(model_name: str) -> str:
    """Generate Zod schema name from model name."""
    return f'{model_name}Schema'


def python_to_graphql_type(python_type: str, required: bool = True) -> str:
    """Convert Python type to GraphQL type."""
    # Basic type mappings
    type_map = {
        'str': 'String',
        'int': 'Int',
        'float': 'Float',
        'bool': 'Boolean',
        'Any': 'JSON',
        'datetime': 'DateTime',
        'date': 'Date',
        'Dict[str, Any]': 'JSON',
    }
    
    # Check basic types
    base_type = python_type
    is_list = False
    is_optional = False
    
    # Handle Optional types
    if python_type.startswith('Optional[') and python_type.endswith(']'):
        base_type = python_type[9:-1]
        is_optional = True
    
    # Handle List types
    if base_type.startswith('List[') and base_type.endswith(']'):
        base_type = base_type[5:-1]
        is_list = True
    
    # Map to GraphQL type
    graphql_type = type_map.get(base_type, base_type)
    
    # Handle list wrapping
    if is_list:
        graphql_type = f'[{graphql_type}]'
    
    # Handle required/optional
    if required and not is_optional:
        graphql_type = f'{graphql_type}!'
    
    return graphql_type


def ts_to_json_schema_type(ts_type: str) -> Dict[str, any]:
    """Convert TypeScript type to JSON Schema type definition."""
    # Basic type mappings
    if ts_type == 'string':
        return {'type': 'string'}
    elif ts_type == 'number':
        return {'type': 'number'}
    elif ts_type == 'boolean':
        return {'type': 'boolean'}
    elif ts_type in ('null', 'undefined'):
        return {'type': 'null'}
    elif ts_type == 'any':
        return {}  # No type constraint
    
    # Arrays
    if ts_type.endswith('[]'):
        inner_type = ts_type[:-2]
        return {
            'type': 'array',
            'items': ts_to_json_schema_type(inner_type)
        }
    
    # Default to string for unknown types
    return {'type': 'string'}