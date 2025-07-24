"""Custom Jinja2 filters for code generation."""
from typing import Any, List, Dict
from jinja2 import Environment


def camel_case(value: str) -> str:
    """Convert snake_case to camelCase."""
    components = value.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def pascal_case(value: str) -> str:
    """Convert snake_case to PascalCase."""
    return ''.join(x.title() for x in value.split('_'))


def snake_case(value: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def title_case(value: str) -> str:
    """Convert snake_case to Title Case."""
    return ' '.join(word.title() for word in value.split('_'))


def pluralize(value: str) -> str:
    """Simple pluralization (add 's' or 'es')."""
    if value.endswith(('s', 'ss', 'sh', 'ch', 'x', 'z')):
        return value + 'es'
    elif value.endswith('y') and len(value) > 1 and value[-2] not in 'aeiou':
        return value[:-1] + 'ies'
    else:
        return value + 's'


def type_to_typescript(type_str: str) -> str:
    """Convert Python/generic type to TypeScript type."""
    type_map = {
        'str': 'string',
        'string': 'string',
        'int': 'number',
        'integer': 'number',
        'float': 'number',
        'number': 'number',
        'bool': 'boolean',
        'boolean': 'boolean',
        'dict': 'Record<string, any>',
        'object': 'Record<string, any>',
        'list': 'any[]',
        'array': 'any[]',
        'any': 'any',
        'null': 'null',
        'undefined': 'undefined',
        'void': 'void'
    }
    
    # Handle generic types like list[str] or dict[str, int]
    if '[' in type_str:
        base_type = type_str.split('[')[0]
        if base_type == 'list' or base_type == 'array':
            inner_type = type_str.split('[')[1].rstrip(']')
            return f"{type_to_typescript(inner_type)}[]"
        elif base_type == 'dict':
            # Simple handling for now
            return 'Record<string, any>'
    
    return type_map.get(type_str.lower(), type_str)


def type_to_python(type_str: str) -> str:
    """Convert generic type to Python type annotation."""
    type_map = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'boolean': 'bool',
        'object': 'Dict[str, Any]',
        'array': 'List[Any]',
        'null': 'None',
        'any': 'Any'
    }
    
    # Handle array types
    if type_str.endswith('[]'):
        inner_type = type_str[:-2]
        return f"List[{type_to_python(inner_type)}]"
    
    return type_map.get(type_str.lower(), type_str)


def get_default_value(field: Dict[str, Any], language: str = 'python') -> Any:
    """Get appropriate default value for a field based on type and language."""
    field_type = field.get('type', 'string')
    
    if field.get('required', False):
        return None
    
    if 'default' in field:
        return field['default']
    
    if language == 'typescript':
        type_defaults = {
            'string': "''",
            'number': '0',
            'boolean': 'false',
            'array': '[]',
            'object': '{}'
        }
    else:  # python
        type_defaults = {
            'string': '""',
            'str': '""',
            'int': '0',
            'integer': '0',
            'float': '0.0',
            'number': '0.0',
            'bool': 'False',
            'boolean': 'False',
            'list': '[]',
            'array': '[]',
            'dict': '{}',
            'object': '{}'
        }
    
    return type_defaults.get(field_type.lower(), 'None' if language == 'python' else 'null')


def indent(text: str, spaces: int = 2) -> str:
    """Indent each line of text by the specified number of spaces."""
    prefix = ' ' * spaces
    return '\n'.join(prefix + line if line else '' for line in text.splitlines())


def register_custom_filters(env: Environment) -> None:
    """Register all custom filters with the Jinja2 environment."""
    env.filters['camel_case'] = camel_case
    env.filters['pascal_case'] = pascal_case
    env.filters['snake_case'] = snake_case
    env.filters['title_case'] = title_case
    env.filters['pluralize'] = pluralize
    env.filters['type_to_typescript'] = type_to_typescript
    env.filters['type_to_python'] = type_to_python
    env.filters['get_default_value'] = get_default_value
    env.filters['indent'] = indent