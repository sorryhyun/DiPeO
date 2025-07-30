"""Template Service with Composition Support

Provides unified template environment setup with shared filters, macros,
and template inheritance while allowing generator-specific customization.
"""

import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from jinja2 import Environment, FileSystemLoader, Template, ChoiceLoader, DictLoader
import inflection


@dataclass
class MacroDefinition:
    """Definition of a reusable template macro"""
    name: str
    template: str
    params: List[str] = field(default_factory=list)
    description: Optional[str] = None


class MacroLibrary:
    """Library of reusable template macros"""
    
    def __init__(self):
        self._macros: Dict[str, MacroDefinition] = {}
        self._register_default_macros()
    
    def register(self, macro: MacroDefinition) -> None:
        """Register a macro in the library"""
        self._macros[macro.name] = macro
    
    def get(self, name: str) -> Optional[MacroDefinition]:
        """Get macro by name"""
        return self._macros.get(name)
    
    def get_all(self) -> Dict[str, MacroDefinition]:
        """Get all registered macros"""
        return self._macros.copy()
    
    def to_template_string(self) -> str:
        """Convert all macros to a template string for inclusion"""
        parts = []
        for macro in self._macros.values():
            params_str = ', '.join(macro.params) if macro.params else ''
            parts.append(f"{{% macro {macro.name}({params_str}) %}}")
            parts.append(macro.template)
            parts.append("{% endmacro %}")
            parts.append("")
        return '\n'.join(parts)
    
    def _register_default_macros(self) -> None:
        """Register default macros"""
        # Python type hint macro
        self.register(MacroDefinition(
            name='python_type_hint',
            template='{{ type_name }}{% if is_optional %} | None{% endif %}',
            params=['type_name', 'is_optional'],
            description='Generate Python type hint with optional support'
        ))
        
        # TypeScript interface property macro
        self.register(MacroDefinition(
            name='ts_property',
            template='{{ name }}{% if is_optional %}?{% endif %}: {{ type_name }}',
            params=['name', 'type_name', 'is_optional'],
            description='Generate TypeScript interface property'
        ))
        
        # GraphQL field macro
        self.register(MacroDefinition(
            name='graphql_field',
            template='{{ name }}: {{ type_name }}{% if not is_required %}{% else %}!{% endif %}',
            params=['name', 'type_name', 'is_required'],
            description='Generate GraphQL field definition'
        ))
        
        # Documentation comment macro
        self.register(MacroDefinition(
            name='doc_comment',
            template="""{% if style == 'python' %}\"\"\"{{ text }}\"\"\"{% elif style == 'js' %}/** {{ text }} */{% elif style == 'graphql' %}\"{{ text }}\"{% endif %}""",
            params=['text', 'style'],
            description='Generate documentation comment in various styles'
        ))


@dataclass
class TemplateRenderer:
    """Renderer for a specific template with custom filters"""
    env: Environment
    template_path: str
    extra_filters: Optional[Dict[str, Callable]] = None
    macro_library: Optional[MacroLibrary] = None
    
    def render(self, **context) -> str:
        """Render the template with given context"""
        # Create a combined environment if we have extra filters
        if self.extra_filters:
            # Clone the environment to avoid modifying the shared one
            local_env = self.env.overlay()
            local_env.filters.update(self.extra_filters)
            template = local_env.get_template(self.template_path)
        else:
            template = self.env.get_template(self.template_path)
        
        # Add macro library to context if available
        if self.macro_library:
            context['macros'] = self.macro_library.get_all()
        
        return template.render(**context)
    
    def render_string(self, template_string: str, **context) -> str:
        """Render a template string with given context"""
        # Include macros if available
        if self.macro_library:
            template_string = self.macro_library.to_template_string() + '\n' + template_string
            context['macros'] = self.macro_library.get_all()
        
        if self.extra_filters:
            local_env = self.env.overlay()
            local_env.filters.update(self.extra_filters)
            template = local_env.from_string(template_string)
        else:
            template = self.env.from_string(template_string)
        
        return template.render(**context)


class SharedFilters:
    """Collection of shared template filters"""
    
    @staticmethod
    def snake_case(text: str) -> str:
        """Convert to snake_case"""
        return inflection.underscore(text)
    
    @staticmethod
    def camel_case(text: str) -> str:
        """Convert to camelCase"""
        return inflection.camelize(text, uppercase_first_letter=False)
    
    @staticmethod
    def pascal_case(text: str) -> str:
        """Convert to PascalCase"""
        return inflection.camelize(text)
    
    @staticmethod
    def kebab_case(text: str) -> str:
        """Convert to kebab-case"""
        return inflection.dasherize(inflection.underscore(text))
    
    @staticmethod
    def pluralize(text: str) -> str:
        """Pluralize a word"""
        return inflection.pluralize(text)
    
    @staticmethod
    def singularize(text: str) -> str:
        """Singularize a word"""
        return inflection.singularize(text)
    
    @staticmethod
    def humanize(text: str) -> str:
        """Convert to human readable form"""
        return inflection.humanize(text)
    
    @staticmethod
    def titleize(text: str) -> str:
        """Convert to Title Case"""
        return inflection.titleize(text)
    
    @staticmethod
    def ordinalize(number: int) -> str:
        """Convert number to ordinal (1st, 2nd, etc.)"""
        return inflection.ordinalize(number)
    
    @staticmethod
    def indent_lines(text: str, spaces: int = 4) -> str:
        """Indent all lines in text"""
        indent = ' ' * spaces
        return '\n'.join(indent + line if line else line 
                        for line in text.splitlines())
    
    @staticmethod
    def quote_string(text: str, quote_char: str = '"') -> str:
        """Quote a string with proper escaping"""
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
        """Join list of strings with separator"""
        return separator.join(items)
    
    @staticmethod
    def json_escape(text: str) -> str:
        """Escape string for JSON"""
        import json
        return json.dumps(text)[1:-1]  # Remove surrounding quotes
    
    @staticmethod
    def regex_replace(text: str, pattern: str, replacement: str) -> str:
        """Replace using regex"""
        return re.sub(pattern, replacement, text)
    
    @staticmethod
    def strip_prefix(text: str, prefix: str) -> str:
        """Remove prefix if present"""
        return text[len(prefix):] if text.startswith(prefix) else text
    
    @staticmethod
    def strip_suffix(text: str, suffix: str) -> str:
        """Remove suffix if present"""
        return text[:-len(suffix)] if text.endswith(suffix) else text
    
    @staticmethod
    def wrap_lines(text: str, width: int = 80) -> str:
        """Wrap long lines"""
        import textwrap
        return textwrap.fill(text, width=width)
    
    @staticmethod
    def default_value(type_name: str, language: str = 'python') -> str:
        """Generate default value for a type"""
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


class TemplateService:
    """Singleton template environment with composition support"""
    
    _instance: Optional['TemplateService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._base_templates: Dict[str, str] = {}
        self._register_base_templates()
        self._env = self._create_base_environment()
        self._register_core_filters()
        self._macro_library = MacroLibrary()
        self._template_cache: Dict[str, Template] = {}
        self._initialized = True
    
    def _create_base_environment(self) -> Environment:
        """Create base Jinja2 environment"""
        # Set up template directories
        template_dirs = [
            Path('files/codegen/templates'),
            Path('files/codegen/templates/models'),
            Path('files/codegen/templates/backend'),
            Path('files/codegen/templates/frontend'),
        ]
        
        # Create loaders
        file_loaders = [FileSystemLoader(str(d)) for d in template_dirs if d.exists()]
        dict_loader = DictLoader(self._base_templates)
        
        # Combine loaders
        loader = ChoiceLoader([dict_loader] + file_loaders)
        
        # Create environment
        env = Environment(
            loader=loader,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        
        return env
    
    def _register_core_filters(self) -> None:
        """Register all core filters"""
        filters = SharedFilters()
        
        # Register all filter methods
        for name in dir(filters):
            if not name.startswith('_'):
                method = getattr(filters, name)
                if callable(method):
                    self._env.filters[name] = method
        
        # Add some aliases for common operations
        self._env.filters['to_snake'] = filters.snake_case
        self._env.filters['to_camel'] = filters.camel_case
        self._env.filters['to_pascal'] = filters.pascal_case
        self._env.filters['to_kebab'] = filters.kebab_case
    
    def _register_base_templates(self) -> None:
        """Register base templates for inheritance"""
        # Python base template
        self._base_templates['python_base.j2'] = """
{%- macro python_imports(imports) -%}
{% for import in imports | sort | unique %}
{{ import }}
{% endfor %}
{%- endmacro -%}

{%- macro python_class(name, bases=[], docstring=None) -%}
class {{ name }}{% if bases %}({{ bases | join(', ') }}){% endif %}:
    {% if docstring %}\"\"\"{{ docstring }}\"\"\"{% endif %}
    {% block class_body %}pass{% endblock %}
{%- endmacro -%}

{% block content %}{% endblock %}
"""
        
        # TypeScript base template
        self._base_templates['typescript_base.j2'] = """
{%- macro ts_imports(imports) -%}
{% for import in imports | sort | unique %}
{{ import }};
{% endfor %}
{%- endmacro -%}

{%- macro ts_interface(name, extends=[]) -%}
export interface {{ name }}{% if extends %} extends {{ extends | join(', ') }}{% endif %} {
    {% block interface_body %}{% endblock %}
}
{%- endmacro -%}

{% block content %}{% endblock %}
"""
        
        # GraphQL base template
        self._base_templates['graphql_base.j2'] = """
{%- macro graphql_type(name, kind='type', implements=[]) -%}
{{ kind }} {{ name }}{% if implements %} implements {{ implements | join(' & ') }}{% endif %} {
    {% block type_body %}{% endblock %}
}
{%- endmacro -%}

{% block content %}{% endblock %}
"""
    
    def get_renderer(
        self,
        template_path: str,
        extra_filters: Optional[Dict[str, Callable]] = None
    ) -> TemplateRenderer:
        """Get a renderer with optional extra filters"""
        return TemplateRenderer(
            env=self._env,
            template_path=template_path,
            extra_filters=extra_filters,
            macro_library=self._macro_library
        )
    
    def add_template_dir(self, directory: Union[str, Path]) -> None:
        """Add a template directory to the loader"""
        directory = Path(directory)
        if directory.exists():
            # Create new loader with additional directory
            current_loader = self._env.loader
            new_file_loader = FileSystemLoader(str(directory))
            
            if isinstance(current_loader, ChoiceLoader):
                current_loader.loaders.append(new_file_loader)
            else:
                self._env.loader = ChoiceLoader([current_loader, new_file_loader])
    
    def register_macro(self, macro: MacroDefinition) -> None:
        """Register a custom macro"""
        self._macro_library.register(macro)
    
    def get_macro_library(self) -> MacroLibrary:
        """Get the macro library"""
        return self._macro_library
    
    def clear_cache(self) -> None:
        """Clear template cache"""
        self._template_cache.clear()
        self._env.cache.clear()
    
    def render_string(self, template_string: str, **context) -> str:
        """Render a template string directly"""
        renderer = self.get_renderer('')
        return renderer.render_string(template_string, **context)
    
    def get_environment(self) -> Environment:
        """Get the Jinja2 environment (for advanced usage)"""
        return self._env