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
        'void': 'void',
        'enum': 'string'  # Default fallback for enum without context
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
        'any': 'Any',
        'enum': 'str'  # Fallback for enum without values context
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


def humanize(value: str) -> str:
    """Convert snake_case or camelCase to human readable format."""
    # First convert camelCase to snake_case
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    # Then convert to title case
    return ' '.join(word.title() for word in s2.split('_'))


def escape_js(value: str) -> str:
    """Escape string for use in JavaScript."""
    if not isinstance(value, str):
        value = str(value)
    return value.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def ui_field_type(field: Dict[str, Any]) -> str:
    """Get UI field type from field definition."""
    ui_config = field.get('uiConfig', {})
    if 'inputType' in ui_config:
        return ui_config['inputType']
    
    # Map field type to UI type
    field_type = field.get('type', 'string')
    type_ui_map = {
        'string': 'text',
        'str': 'text',
        'text': 'textarea',
        'number': 'number',
        'int': 'number',
        'integer': 'number',
        'float': 'number',
        'bool': 'checkbox',
        'boolean': 'checkbox',
        'array': 'code',
        'list': 'code',
        'object': 'code',
        'dict': 'code',
        'enum': 'select',
        'select': 'select',
        'date': 'date',
        'datetime': 'datetime',
        'time': 'time',
        'file': 'file',
        'password': 'password',
        'email': 'email',
        'url': 'url',
        'color': 'color'
    }
    
    return type_ui_map.get(field_type, 'text')


def typescript_type(field: Dict[str, Any]) -> str:
    """Get TypeScript type from field definition."""
    field_type = field.get('type', 'string')
    
    # Special handling for enum fields with values
    if field_type == 'enum' and 'values' in field:
        values = field.get('values', [])
        if values:
            # Generate union type from enum values
            return ' | '.join(f"'{v}'" for v in values)
        else:
            return 'string'  # Fallback if no values specified
    
    return map_to_typescript_type(field_type)


def zod_schema(field: Dict[str, Any]) -> str:
    """Generate Zod schema for field validation."""
    field_type = field.get('type', 'string')
    required = field.get('required', False)
    
    # Special handling for enum fields
    if field_type == 'enum' and 'values' in field:
        values = field.get('values', [])
        if values:
            # Generate z.enum() for enum fields
            enum_values = ', '.join(f'"{v}"' for v in values)
            base_schema = f'z.enum([{enum_values}])'
        else:
            base_schema = 'z.string()'
    else:
        # Base schemas for other types
        schema_map = {
            'string': 'z.string()',
            'str': 'z.string()',
            'text': 'z.string()',
            'number': 'z.number()',
            'int': 'z.number()',
            'integer': 'z.number()',
            'float': 'z.number()',
            'bool': 'z.boolean()',
            'boolean': 'z.boolean()',
            'array': 'z.array(z.any())',
            'list': 'z.array(z.any())',
            'object': 'z.record(z.any())',
            'dict': 'z.record(z.any())',
            'any': 'z.any()',
            'null': 'z.null()',
            'undefined': 'z.undefined()'
        }
        
        base_schema = schema_map.get(field_type, 'z.any()')
    
    # Add validation
    validations = []
    if field.get('validation'):
        val = field['validation']
        if 'min' in val:
            validations.append(f'.min({val["min"]})')
        if 'max' in val:
            validations.append(f'.max({val["max"]})')
        if 'pattern' in val:
            # Escape forward slashes in the pattern for JavaScript regex literal
            escaped_pattern = val["pattern"].replace('/', '\\/')
            validations.append(f'.regex(/{escaped_pattern}/)')
    
    schema = base_schema + ''.join(validations)
    
    # Handle optional
    if not required:
        schema += '.optional()'
    
    return schema


def map_to_typescript_type(type_str: str) -> str:
    """Map generic type to TypeScript type."""
    return type_to_typescript(type_str)


def graphql_type(field: Dict[str, Any]) -> str:
    """Convert field type to GraphQL type."""
    field_type = field.get('type', 'string')
    required = field.get('required', False)
    
    # Map to GraphQL scalar types
    type_map = {
        'string': 'String',
        'str': 'String',
        'text': 'String',
        'int': 'Int',
        'integer': 'Int',
        'float': 'Float',
        'number': 'Float',
        'bool': 'Boolean',
        'boolean': 'Boolean',
        'id': 'ID',
        'date': 'String',
        'datetime': 'String',
        'time': 'String',
        'json': 'JSON',
        'any': 'JSON',
        'object': 'JSON',
        'dict': 'JSON',
        'list': '[JSON]',
        'array': '[JSON]',
        'enum': 'String'  # Map enum to String for now
    }
    
    # Handle array types
    if field_type.endswith('[]'):
        inner_type = field_type[:-2]
        base_type = type_map.get(inner_type, 'JSON')
        gql_type = f'[{base_type}]'
    else:
        gql_type = type_map.get(field_type.lower(), 'String')
    
    # Add required modifier
    if required:
        gql_type += '!'
    
    return gql_type


def python_type(field: Dict[str, Any]) -> str:
    """Get Python type annotation from field definition."""
    field_type = field.get('type', 'string')
    field_name = field.get('name', '')
    
    # Map specific field names to their enum types
    enum_mappings = {
        'operation': {
            'notion': 'NotionOperation',
            'default': 'str'
        },
        'sub_type': 'DBBlockSubType',
        'method': 'HttpMethod',
        'language': 'SupportedLanguage',
        'code_type': 'SupportedLanguage',
        'hook_type': 'HookType',
        'trigger_mode': 'HookTriggerMode',
        'service': 'LLMService',
        'api_service_type': 'APIServiceType',
        'condition_type': 'str',  # Keep as string for now
        'format': 'DiagramFormat',
        'diagram_format': 'DiagramFormat'
    }
    
    # Check if this field has a specific enum mapping
    if field_name in enum_mappings:
        mapping = enum_mappings[field_name]
        if isinstance(mapping, dict):
            # Context-specific mapping (e.g., operation depends on node type)
            # We'd need to pass context, for now use default
            return mapping.get('default', 'str')
        else:
            return mapping
    
    # Handle special cases
    if field_type == 'json' or field_type == 'object':
        return 'Dict[str, Any]'
    elif field_type == 'array' or field_type == 'list':
        return 'List[Any]'
    elif field_type == 'enum':
        # For enum fields, use Literal type with the allowed values
        values = field.get('values', [])
        if values:
            # Format values as quoted strings for Literal
            quoted_values = ', '.join(f'"{v}"' for v in values)
            return f'Literal[{quoted_values}]'
        else:
            return 'str'  # Fallback to str if no values specified
    
    return type_to_python(field_type)


def python_default(field: Dict[str, Any]) -> str:
    """Get Python default value from field definition."""
    if field.get('required', False):
        # Required fields don't have defaults in dataclass
        return ''
    
    field_type = field.get('type', 'string')
    
    if 'default' in field:
        default = field['default']
        if isinstance(default, str):
            return f'"{default}"'
        elif isinstance(default, bool):
            return 'True' if default else 'False'
        else:
            return str(default)
    
    # For mutable types (dict, list), use field(default_factory=...)
    if field_type in ['object', 'dict', 'json']:
        return 'field(default_factory=dict)'
    elif field_type in ['array', 'list']:
        return 'field(default_factory=list)'
    
    # For enum fields with Literal type, we need special handling
    if field_type == 'enum' and 'values' in field and field.get('values'):
        # For optional enum fields, use the first value as default
        first_value = field['values'][0]
        return f'"{first_value}"'
    
    # Get type-based default
    default_val = get_default_value(field, 'python')
    
    # For optional fields without explicit default, use empty string for strings
    if default_val == '""':
        return '""'
    elif default_val is None:
        return 'None'
    
    return default_val

def is_enum(type_str: str) -> bool:
    """Check if a type string represents an enum."""
    # Simple check - could be expanded based on actual enum tracking
    return type_str.lower() == 'enum' or type_str.endswith('Enum')


def ends_with(value: str, suffix: str) -> bool:
    """Check if string ends with suffix."""
    return value.endswith(suffix)


def to_node_type(value: str) -> str:
    """Convert class name to node type."""
    # Remove 'NodeData' or 'Node' suffix and convert to snake_case
    if value.endswith('NodeData'):
        base = value[:-8]
    elif value.endswith('Node'):
        base = value[:-4]
    else:
        base = value
    
    # Convert to snake_case
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', base)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def python_type_with_context(field: Dict[str, Any], node_type: str = '') -> str:
    """Get Python type annotation with node type context."""
    field_type = field.get('type', 'string')
    field_name = field.get('name', '')
    
    # Map specific field names to their enum types with node context
    enum_mappings = {
        'operation': {
            'notion': 'NotionOperation',
            'api_job': 'str',  # API operations are flexible
            'db': 'str',  # DB operations are flexible
            'default': 'str'
        },
        'sub_type': 'DBBlockSubType',
        'method': 'HttpMethod',
        'language': 'SupportedLanguage',
        'code_type': 'SupportedLanguage',
        'hook_type': 'HookType',
        'trigger_mode': 'HookTriggerMode',
        'service': 'LLMService',
        'api_service_type': 'APIServiceType',
        'condition_type': 'str',  # Keep as string for now
        'format': 'DiagramFormat',
        'diagram_format': 'DiagramFormat'
    }
    
    # Check if this field has a specific enum mapping
    if field_name in enum_mappings:
        mapping = enum_mappings[field_name]
        if isinstance(mapping, dict):
            # Context-specific mapping (e.g., operation depends on node type)
            return mapping.get(node_type, mapping.get('default', 'str'))
        else:
            return mapping
    
    # Delegate to the original python_type function for other cases
    return python_type(field)


from files.codegen.code.shared.emoji_filters import emoji_to_icon
def register_custom_filters(env: Environment) -> None:
    """Register all custom filters with the Jinja2 environment."""
    env.filters['camel_case'] = camel_case
    env.filters['camelCase'] = camel_case  # Alias
    env.filters['pascal_case'] = pascal_case
    env.filters['snake_case'] = snake_case
    env.filters['snakeCase'] = snake_case  # Alias for template compatibility
    env.filters['title_case'] = title_case
    env.filters['pluralize'] = pluralize
    env.filters['type_to_typescript'] = type_to_typescript
    env.filters['type_to_python'] = type_to_python
    env.filters['get_default_value'] = get_default_value
    env.filters['indent'] = indent
    env.filters['humanize'] = humanize
    env.filters['escape_js'] = escape_js
    env.filters['emoji_to_icon'] = emoji_to_icon
    env.filters['ui_field_type'] = ui_field_type
    env.filters['typescript_type'] = typescript_type
    env.filters['zod_schema'] = zod_schema
    env.filters['graphql_type'] = graphql_type
    env.filters['python_type'] = python_type
    env.filters['python_default'] = python_default
    env.filters['python_type_with_context'] = python_type_with_context
    env.filters['isEnum'] = is_enum
    env.filters['endsWith'] = ends_with
    env.filters['toNodeType'] = to_node_type