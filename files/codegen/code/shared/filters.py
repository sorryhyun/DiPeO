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


def emoji_to_icon(emoji: str) -> str:
    """Convert emoji to icon name (for lucide-react)."""
    emoji_icon_map = {
        '🤖': 'Bot',
        '📝': 'FileText',
        '💾': 'Database',
        '🔧': 'Wrench',
        '⚡': 'Zap',
        '🔄': 'RefreshCw',
        '🌐': 'Globe',
        '📊': 'BarChart',
        '📈': 'TrendingUp',
        '🔍': 'Search',
        '⚙️': 'Settings',
        '📁': 'Folder',
        '📂': 'FolderOpen',
        '🚀': 'Rocket',
        '🎯': 'Target',
        '✅': 'Check',
        '❌': 'X',
        '⏱️': 'Timer',
        '📅': 'Calendar',
        '💡': 'Lightbulb',
        '🔐': 'Lock',
        '🔓': 'Unlock',
        '📧': 'Mail',
        '💬': 'MessageSquare',
        '👤': 'User',
        '👥': 'Users',
        '🏷️': 'Tag',
        '📎': 'Paperclip',
        '🔗': 'Link',
        '⚠️': 'AlertTriangle',
        'ℹ️': 'Info',
        '❓': 'HelpCircle',
        '🎨': 'Palette',
        '📸': 'Camera',
        '🎵': 'Music',
        '🎬': 'Film',
        '📺': 'Tv',
        '📻': 'Radio',
        '🔊': 'Volume2',
        '🔇': 'VolumeX',
        '🔔': 'Bell',
        '🔕': 'BellOff',
        '📍': 'MapPin',
        '🗺️': 'Map',
        '🧭': 'Compass',
        '🏠': 'Home',
        '🏢': 'Building',
        '🏭': 'Factory',
        '🏥': 'Building2',
        '🏦': 'Landmark',
        '✈️': 'Plane',
        '🚗': 'Car',
        '🚌': 'Bus',
        '🚆': 'Train',
        '🚢': 'Ship',
        '🚁': 'Plane',
        '⏰': 'Clock',
        '⌚': 'Watch',
        '📱': 'Smartphone',
        '💻': 'Laptop',
        '🖥️': 'Monitor',
        '🖨️': 'Printer',
        '⌨️': 'Keyboard',
        '🖱️': 'Mouse',
        '💿': 'Disc',
        '💵': 'DollarSign',
        '💳': 'CreditCard',
        '📉': 'TrendingDown',
        '📊': 'BarChart2',
        '📋': 'Clipboard',
        '📌': 'Pin',
        '📏': 'Ruler',
        '✂️': 'Scissors',
        '🖊️': 'Pen',
        '✏️': 'Pencil',
        '📚': 'BookOpen',
        '📖': 'Book',
        '🔖': 'Bookmark',
        '🏷️': 'Tags',
        '🎁': 'Gift',
        '🎉': 'PartyPopper',
        '🎈': 'Sparkles',
        '🎯': 'Target',
        '🏆': 'Trophy',
        '🥇': 'Medal',
        '⚽': 'Circle',
        '🏀': 'Circle',
        '🎾': 'Circle',
        '🎮': 'Gamepad2',
        '🎲': 'Dices',
        '🧩': 'Puzzle',
        '🔥': 'Flame',
        '💧': 'Droplet',
        '🌟': 'Star',
        '⭐': 'Star',
        '🌙': 'Moon',
        '☀️': 'Sun',
        '⛅': 'CloudSun',
        '☁️': 'Cloud',
        '🌧️': 'CloudRain',
        '⛈️': 'CloudLightning',
        '❄️': 'Snowflake',
        '🌈': 'Rainbow',
        '🌊': 'Waves',
        '🍃': 'Leaf',
        '🌺': 'Flower',
        '🌻': 'Flower2',
        '🌲': 'Trees',
        '🌳': 'TreePine',
        '🌴': 'Palmtree',
        '🌵': 'Cactus',
        '🍀': 'Clover',
        '🍄': 'Mushroom',
        '🌰': 'Nut',
        '🦋': 'Bug',
        '🐛': 'Bug',
        '🐝': 'Bug',
        '🐞': 'Bug',
        '🦗': 'Bug',
        '🕷️': 'Bug',
        '🦂': 'Bug',
        '🐢': 'Turtle',
        '🐍': 'Worm',
        '🦎': 'Fish',
        '🦖': 'Fish',
        '🦕': 'Fish',
        '🐙': 'Fish',
        '🦑': 'Fish',
        '🦐': 'Fish',
        '🦞': 'Fish',
        '🦀': 'Fish',
        '🐡': 'Fish',
        '🐠': 'Fish',
        '🐟': 'Fish',
        '🐬': 'Fish',
        '🐳': 'Fish',
        '🐋': 'Fish',
        '🦈': 'Fish',
        '🐊': 'Fish',
        '🐅': 'Cat',
        '🐆': 'Cat',
        '🦓': 'GitBranch',
        '🦍': 'User',
        '🦧': 'User',
        '🦣': 'Database',
        '🐘': 'Database',
        '🦛': 'Database',
        '🦏': 'Shield',
        '🐪': 'Mountain',
        '🐫': 'Mountain',
        '🦒': 'GitCommit',
        '🦘': 'Activity',
        '🦬': 'HardDrive',
        '🐃': 'HardDrive',
        '🐂': 'HardDrive',
        '🐄': 'HardDrive',
        '🐎': 'Zap',
        '🐖': 'Package',
        '🐏': 'Cloud',
        '🐑': 'Cloud',
        '🦙': 'Layers',
        '🐐': 'Triangle',
        '🦌': 'GitBranch',
        '🐕': 'Heart',
        '🐩': 'Heart',
        '🦮': 'Eye',
        '🐕‍🦺': 'Shield',
        '🐈': 'Cat',
        '🐈‍⬛': 'Moon',
        '🐓': 'Sun',
        '🦃': 'Package',
        '🦆': 'Droplet',
        '🦢': 'Feather',
        '🦅': 'Send',
        '🦉': 'Moon',
        '🦇': 'Moon',
        '🐺': 'AlertTriangle',
        '🦊': 'Cpu',
        '🦝': 'Eye',
        '🐗': 'Package',
        '🐴': 'Zap',
        '🦄': 'Sparkles',
        '🐝': 'Hexagon',
        '🐛': 'Bug',
        '🦋': 'Wind',
        '🐌': 'Loader',
        '🐞': 'Bug',
        '🐜': 'Activity',
        '🦟': 'Radio',
        '🦗': 'Radio',
        '🕷️': 'Globe',
        '🦂': 'AlertTriangle',
        '🐢': 'Shield',
        '🐍': 'GitCommit',
        '🦎': 'Activity',
        '🦖': 'AlertTriangle',
        '🦕': 'BarChart',
        '🐙': 'GitBranch',
        '🦑': 'GitMerge',
        '🦐': 'MoreHorizontal',
        '🦞': 'Scissors',
        '🦀': 'Move',
        '🐡': 'Circle',
        '🐠': 'Fish',
        '🐟': 'Fish',
        '🐬': 'Activity',
        '🐳': 'Database',
        '🐋': 'Database',
        '🦈': 'AlertTriangle',
        '🐊': 'AlertTriangle',
        '🐅': 'Zap',
        '🐆': 'Zap',
        '🦓': 'BarChart',
        '🦍': 'Shield',
        '🦧': 'User',
        '🦣': 'Database',
        '🐘': 'Database',
        '🦛': 'Package',
        '🦏': 'Shield',
        '🐪': 'BarChart',
        '🐫': 'BarChart',
        '🦒': 'GitCommit',
        '🦘': 'Activity',
        '🦬': 'HardDrive',
        '🐃': 'HardDrive',
        '🐂': 'HardDrive',
        '🐄': 'Package',
        '🐎': 'Zap',
        '🐖': 'Package',
        '🐏': 'Cloud',
        '🐑': 'Cloud',
        '🦙': 'Layers',
        '🐐': 'Triangle',
        '🦌': 'GitBranch',
        '🐕': 'Heart',
        '🐩': 'Scissors',
        '🦮': 'Eye',
        '🐕‍🦺': 'Shield',
        '🐈': 'Hash',
        '🐈‍⬛': 'Moon',
        '🪶': 'Feather',
        '🐓': 'Sun',
        '🦃': 'Package',
        '🦆': 'Droplet',
        '🦢': 'Feather',
        '🦅': 'Send',
        '🦉': 'Moon',
        '🦇': 'Moon',
        '🐺': 'AlertTriangle',
        '🦊': 'Cpu',
        '🦝': 'Eye',
        '🐗': 'Package',
        '🐴': 'Zap',
        '🦄': 'Sparkles',
    }
    return emoji_icon_map.get(emoji, 'Circle')


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
    return map_to_typescript_type(field.get('type', 'string'))


def zod_schema(field: Dict[str, Any]) -> str:
    """Generate Zod schema for field validation."""
    field_type = field.get('type', 'string')
    required = field.get('required', False)
    
    # Base schemas
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
            validations.append(f'.regex(/{val["pattern"]}/)')
    
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
        'array': '[JSON]'
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
    
    # Handle special cases
    if field_type == 'json' or field_type == 'object':
        return 'Dict[str, Any]'
    elif field_type == 'array' or field_type == 'list':
        return 'List[Any]'
    
    return type_to_python(field_type)


def python_default(field: Dict[str, Any]) -> str:
    """Get Python default value from field definition."""
    if field.get('required', False):
        # Required fields don't have defaults in Pydantic
        return ''
    
    if 'default' in field:
        default = field['default']
        if isinstance(default, str):
            return f'"{default}"'
        elif isinstance(default, bool):
            return 'True' if default else 'False'
        else:
            return str(default)
    
    # Get type-based default
    default_val = get_default_value(field, 'python')
    
    # For optional fields without explicit default, use None
    if default_val is None:
        return 'None'
    
    return default_val


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
    env.filters['humanize'] = humanize
    env.filters['escape_js'] = escape_js
    env.filters['emoji_to_icon'] = emoji_to_icon
    env.filters['ui_field_type'] = ui_field_type
    env.filters['typescript_type'] = typescript_type
    env.filters['zod_schema'] = zod_schema
    env.filters['graphql_type'] = graphql_type
    env.filters['python_type'] = python_type
    env.filters['python_default'] = python_default