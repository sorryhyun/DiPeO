"""Template service with composable filters, macros, and template inheritance."""

import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from jinja2 import Environment, FileSystemLoader, Template, ChoiceLoader, DictLoader

from .filters import FilterRegistry, create_filter_registry_profile


@dataclass
class MacroDefinition:
    name: str
    template: str
    params: List[str] = field(default_factory=list)
    description: Optional[str] = None


class MacroLibrary:
    
    def __init__(self):
        self._macros: Dict[str, MacroDefinition] = {}
        self._register_default_macros()
    
    def register(self, macro: MacroDefinition) -> None:
        self._macros[macro.name] = macro
    
    def get(self, name: str) -> Optional[MacroDefinition]:
        return self._macros.get(name)
    
    def get_all(self) -> Dict[str, MacroDefinition]:
        return self._macros.copy()
    
    def to_template_string(self) -> str:
        parts = []
        for macro in self._macros.values():
            params_str = ', '.join(macro.params) if macro.params else ''
            parts.append(f"{{% macro {macro.name}({params_str}) %}}")
            parts.append(macro.template)
            parts.append("{% endmacro %}")
            parts.append("")
        return '\n'.join(parts)
    
    def _register_default_macros(self) -> None:
        self.register(MacroDefinition(
            name='python_type_hint',
            template='{{ type_name }}{% if is_optional %} | None{% endif %}',
            params=['type_name', 'is_optional'],
            description='Generate Python type hint with optional support'
        ))
        
        self.register(MacroDefinition(
            name='ts_property',
            template='{{ name }}{% if is_optional %}?{% endif %}: {{ type_name }}',
            params=['name', 'type_name', 'is_optional'],
            description='Generate TypeScript interface property'
        ))
        
        self.register(MacroDefinition(
            name='graphql_field',
            template='{{ name }}: {{ type_name }}{% if not is_required %}{% else %}!{% endif %}',
            params=['name', 'type_name', 'is_required'],
            description='Generate GraphQL field definition'
        ))
        
        self.register(MacroDefinition(
            name='doc_comment',
            template="""{% if style == 'python' %}\"\"\"{{ text }}\"\"\"{% elif style == 'js' %}/** {{ text }} */{% elif style == 'graphql' %}\"{{ text }}\"{% endif %}""",
            params=['text', 'style'],
            description='Generate documentation comment in various styles'
        ))


@dataclass
class TemplateRenderer:
    env: Environment
    template_path: str
    extra_filters: Optional[Dict[str, Callable]] = None
    macro_library: Optional[MacroLibrary] = None
    
    def render(self, **context) -> str:
        if self.extra_filters:
            local_env = self.env.overlay()
            local_env.filters.update(self.extra_filters)
            template = local_env.get_template(self.template_path)
        else:
            template = self.env.get_template(self.template_path)
        
        if self.macro_library:
            context['macros'] = self.macro_library.get_all()
        
        return template.render(**context)
    
    def render_string(self, template_string: str, **context) -> str:
        if self.macro_library:
            template_string = self.macro_library.to_template_string() + '\n' + template_string
            context['macros'] = self.macro_library.get_all()
        
        if self.extra_filters:
            local_env = self.env.overlay()
            local_env.filters.update(self.extra_filters)
            template = local_env.from_string(template_string)
        else:
            template = self.env.from_string(template_string)
        
        result = template.render(**context)
        return result


class TemplateService:
    
    def __init__(self, filter_sources: Optional[List[str]] = None, profile: str = 'full'):
        
        self._base_templates: Dict[str, str] = {}
        self._register_base_templates()
        
        self._filter_registry = create_filter_registry_profile(profile)
        
        if filter_sources is None:
            filter_sources = ['base']
        self._filter_sources = filter_sources
        
        self._env = self._create_base_environment()
        self._register_filters()
        
        self._macro_library = MacroLibrary()
        self._template_cache: Dict[str, Template] = {}
    
    def _create_base_environment(self) -> Environment:
        template_dirs = [
            Path('projects/codegen/templates'),
            Path('projects/codegen/templates/models'),
            Path('projects/codegen/templates/backend'),
            Path('projects/codegen/templates/frontend'),
        ]
        
        file_loaders = [FileSystemLoader(str(d)) for d in template_dirs if d.exists()]
        dict_loader = DictLoader(self._base_templates)
        loader = ChoiceLoader([dict_loader] + file_loaders)
        
        env = Environment(
            loader=loader,
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=True,
        )
        
        return env
    
    def _register_filters(self) -> None:
        filters = self._filter_registry.compose_filters(*self._filter_sources)
        
        for name, function in filters.items():
            self._env.filters[name] = function
        
        if 'base' in self._filter_sources:
            self._env.filters['to_snake'] = self._env.filters.get('snake_case')
            self._env.filters['to_camel'] = self._env.filters.get('camel_case')
            self._env.filters['to_pascal'] = self._env.filters.get('pascal_case')
            self._env.filters['to_kebab'] = self._env.filters.get('kebab_case')
    
    def _register_base_templates(self) -> None:
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
        
        self._base_templates['graphql_base.j2'] = """
{%- macro graphql_type(name, kind='type', implements=[]) -%}
{{ kind }} {{ name }}{% if implements %} implements {{ implements | join(' & ') }}{% endif %} {
    {% block type_body %}{% endblock %}
}
{%- endmacro -%}

{% block content %}{% endblock %}
"""
    
    def add_filter_source(self, source: str) -> None:
        if source not in self._filter_sources:
            self._filter_sources.append(source)
            self._register_filters()
    
    def remove_filter_source(self, source: str) -> None:
        if source in self._filter_sources:
            self._filter_sources.remove(source)
            self._env.filters.clear()
            self._register_filters()
    
    def get_renderer(
        self,
        template_path: str,
        extra_filters: Optional[Dict[str, Callable]] = None
    ) -> TemplateRenderer:
        return TemplateRenderer(
            env=self._env,
            template_path=template_path,
            extra_filters=extra_filters,
            macro_library=self._macro_library
        )
    
    def add_template_dir(self, directory: Union[str, Path]) -> None:
        directory = Path(directory)
        if directory.exists():
            current_loader = self._env.loader
            new_file_loader = FileSystemLoader(str(directory))
            
            if isinstance(current_loader, ChoiceLoader):
                current_loader.loaders.append(new_file_loader)
            else:
                self._env.loader = ChoiceLoader([current_loader, new_file_loader])
    
    def register_macro(self, macro: MacroDefinition) -> None:
        self._macro_library.register(macro)
    
    def get_macro_library(self) -> MacroLibrary:
        return self._macro_library
    
    def clear_cache(self) -> None:
        self._template_cache.clear()
        if hasattr(self._env, 'cache'):
            self._env.cache.clear()
    
    def render_string(self, template_string: str, **context) -> str:
        renderer = self.get_renderer('')
        return renderer.render_string(template_string, **context)
    
    def get_environment(self) -> Environment:
        return self._env
    
    def get_active_filters(self) -> List[str]:
        return self._filter_sources.copy()


def create_template_service(filter_sources: Optional[List[str]] = None, profile: str = 'full') -> TemplateService:
    return TemplateService(filter_sources, profile=profile)