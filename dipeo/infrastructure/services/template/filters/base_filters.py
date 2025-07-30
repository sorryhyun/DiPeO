"""Base template filters for general-purpose text transformations.

These filters provide common string manipulation operations that are useful
across different template contexts (Python, TypeScript, GraphQL, etc.).
"""

import re
import inflection
from typing import List, Any


class BaseFilters:
    """Collection of base template filters for text transformation."""
    
    @staticmethod
    def snake_case(text: str) -> str:
        """Convert to snake_case."""
        if text is None or text == '' or str(text) == 'Undefined':
            return ''
        return inflection.underscore(str(text))
    
    @staticmethod
    def camel_case(text: str) -> str:
        """Convert to camelCase."""
        return inflection.camelize(text, uppercase_first_letter=False)
    
    @staticmethod
    def pascal_case(text: str) -> str:
        """Convert to PascalCase."""
        return inflection.camelize(text)
    
    @staticmethod
    def kebab_case(text: str) -> str:
        """Convert to kebab-case."""
        return inflection.dasherize(inflection.underscore(text))
    
    @staticmethod
    def pluralize(text: str) -> str:
        """Pluralize a word."""
        return inflection.pluralize(text)
    
    @staticmethod
    def singularize(text: str) -> str:
        """Singularize a word."""
        return inflection.singularize(text)
    
    @staticmethod
    def humanize(text: str) -> str:
        """Convert to human readable form."""
        return inflection.humanize(text)
    
    @staticmethod
    def titleize(text: str) -> str:
        """Convert to Title Case."""
        return inflection.titleize(text)
    
    @staticmethod
    def ordinalize(number: int) -> str:
        """Convert number to ordinal (1st, 2nd, etc.)."""
        return inflection.ordinalize(number)
    
    @staticmethod
    def indent_lines(text: str, spaces: int = 4) -> str:
        """Indent all lines in text."""
        indent = ' ' * spaces
        return '\n'.join(indent + line if line else line 
                        for line in text.splitlines())
    
    @staticmethod
    def quote_string(text: str, quote_char: str = '"') -> str:
        """Quote a string with proper escaping."""
        if quote_char == '"':
            escaped = text.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        elif quote_char == "'":
            escaped = text.replace('\\', '\\\\').replace("'", "\\'")
            return f"'{escaped}'"
        else:
            return text
    
    @staticmethod
    def join_lines(items: List[str], separator: str = '\n') -> str:
        """Join list of strings with separator."""
        return separator.join(items)
    
    @staticmethod
    def json_escape(text: str) -> str:
        """Escape string for JSON."""
        import json
        return json.dumps(text)[1:-1]  # Remove surrounding quotes
    
    @staticmethod
    def regex_replace(text: str, pattern: str, replacement: str) -> str:
        """Replace using regex."""
        return re.sub(pattern, replacement, text)
    
    @staticmethod
    def strip_prefix(text: str, prefix: str) -> str:
        """Remove prefix if present."""
        return text[len(prefix):] if text.startswith(prefix) else text
    
    @staticmethod
    def strip_suffix(text: str, suffix: str) -> str:
        """Remove suffix if present."""
        return text[:-len(suffix)] if text.endswith(suffix) else text
    
    @staticmethod
    def wrap_lines(text: str, width: int = 80) -> str:
        """Wrap long lines."""
        import textwrap
        return textwrap.fill(text, width=width)
    
    @staticmethod
    def default_value(type_name: str, language: str = 'python') -> str:
        """Generate default value for a type."""
        defaults = {
            'python': {
                'str': '""',
                'int': '0',
                'float': '0.0',
                'bool': 'False',
                'list': '[]',
                'dict': '{}',
                'set': 'set()',
                'tuple': '()',
                'None': 'None',
            },
            'typescript': {
                'string': '""',
                'number': '0',
                'boolean': 'false',
                'array': '[]',
                'object': '{}',
                'null': 'null',
                'undefined': 'undefined',
            },
            'graphql': {
                'String': '""',
                'Int': '0',
                'Float': '0.0',
                'Boolean': 'false',
                'ID': '""',
            }
        }
        
        lang_defaults = defaults.get(language, {})
        return lang_defaults.get(type_name, 'null' if language == 'typescript' else 'None')
    
    @classmethod
    def get_all_filters(cls) -> dict:
        """Get all filter methods as a dictionary."""
        filters = {}
        for name in dir(cls):
            if not name.startswith('_') and name != 'get_all_filters':
                method = getattr(cls, name)
                if callable(method):
                    filters[name] = method
        return filters