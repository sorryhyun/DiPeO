"""Template utilities for code generation."""

import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_jinja_env(template_dir):
    """Create a Jinja2 environment with common filters."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add case conversion filters
    env.filters['camelCase'] = camel_case
    env.filters['PascalCase'] = pascal_case
    env.filters['snake_case'] = snake_case
    env.filters['snakeCase'] = snake_case  # Alias for backward compatibility
    env.filters['UPPER_CASE'] = lambda text: snake_case(text).upper()
    
    # Add utility filters
    env.filters['endsWith'] = lambda text, suffix: str(text).endswith(suffix)
    env.filters['startsWith'] = lambda text, prefix: str(text).startswith(prefix)
    
    return env


def register_enum_filter(env, enum_data):
    """Register enum filtering function in Jinja environment."""
    def is_enum(type_name):
        """Check if a type name is an enum."""
        # Handle both simple and array types
        clean_type = type_name.replace('[]', '').strip()
        return clean_type in [enum['name'] for enum in enum_data]
    
    env.filters['is_enum'] = is_enum
    env.filters['isEnum'] = is_enum  # Alias for backward compatibility


# Case conversion functions
def snake_case(text: str) -> str:
    """Convert to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', str(text))
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def camel_case(text: str) -> str:
    """Convert to camelCase."""
    words = re.split(r'[\s_\-]+', str(text))
    if not words:
        return ''
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])


def pascal_case(text: str) -> str:
    """Convert to PascalCase."""
    words = re.split(r'[\s_\-]+', str(text))
    return ''.join(w.capitalize() for w in words)