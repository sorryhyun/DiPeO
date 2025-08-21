"""Macro library for template processing."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MacroDefinition:
    """Definition of a template macro."""
    name: str
    template: str
    params: List[str] = field(default_factory=list)
    description: Optional[str] = None


class MacroLibrary:
    """Library of reusable template macros.
    
    Macros are template fragments that can be called with parameters,
    similar to functions in programming languages.
    """
    
    def __init__(self):
        """Initialize the macro library with default macros."""
        self._macros: Dict[str, MacroDefinition] = {}
        self._register_default_macros()
    
    def register(self, macro: MacroDefinition) -> None:
        """Register a macro in the library.
        
        Args:
            macro: The macro definition to register
        """
        self._macros[macro.name] = macro
    
    def get(self, name: str) -> Optional[MacroDefinition]:
        """Get a macro by name.
        
        Args:
            name: The name of the macro
            
        Returns:
            The macro definition if found, None otherwise
        """
        return self._macros.get(name)
    
    def get_all(self) -> Dict[str, MacroDefinition]:
        """Get all registered macros.
        
        Returns:
            Dictionary of all macros
        """
        return self._macros.copy()
    
    def to_template_string(self) -> str:
        """Convert all macros to Jinja2 template syntax.
        
        Returns:
            String containing all macro definitions in Jinja2 format
        """
        parts = []
        for macro in self._macros.values():
            params_str = ', '.join(macro.params) if macro.params else ''
            parts.append(f"{{% macro {macro.name}({params_str}) %}}")
            parts.append(macro.template)
            parts.append("{% endmacro %}")
            parts.append("")
        return '\n'.join(parts)
    
    def _register_default_macros(self) -> None:
        """Register default macros for common code generation patterns."""
        # Python type hint macro
        self.register(MacroDefinition(
            name='python_type_hint',
            template='{{ type_name }}{% if is_optional %} | None{% endif %}',
            params=['type_name', 'is_optional'],
            description='Generate Python type hint with optional support'
        ))
        
        # TypeScript property macro
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
        
        # Python class macro
        self.register(MacroDefinition(
            name='python_class',
            template="""class {{ name }}{% if bases %}({{ bases | join(', ') }}){% endif %}:
    {% if docstring %}\"\"\"{{ docstring }}\"\"\"{% endif %}""",
            params=['name', 'bases', 'docstring'],
            description='Generate Python class definition'
        ))
        
        # TypeScript interface macro
        self.register(MacroDefinition(
            name='ts_interface',
            template="""export interface {{ name }}{% if extends %} extends {{ extends | join(', ') }}{% endif %} {""",
            params=['name', 'extends'],
            description='Generate TypeScript interface definition'
        ))
        
        # Import statement macro
        self.register(MacroDefinition(
            name='import_statement',
            template="""{% if style == 'python' %}from {{ module }} import {{ items | join(', ') }}{% elif style == 'typescript' %}import { {{ items | join(', ') }} } from '{{ module }}';{% endif %}""",
            params=['module', 'items', 'style'],
            description='Generate import statements for different languages'
        ))