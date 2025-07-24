"""Shared template environment creation for codegen."""
from jinja2 import Environment, BaseLoader
from typing import Dict, Any
from .filters import register_custom_filters


class StringLoader(BaseLoader):
    """Loader that loads templates from strings."""
    
    def get_source(self, environment, template):
        # In our case, the template is the actual content
        return template, None, lambda: True


def create_template_env() -> Environment:
    """Create a Jinja2 environment with custom filters for code generation."""
    env = Environment(
        loader=StringLoader(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )
    
    # Register custom filters
    register_custom_filters(env)
    
    return env


def render_template(template_content: str, context: Dict[str, Any]) -> str:
    """Render a template string with the given context."""
    env = create_template_env()
    template = env.from_string(template_content)
    return template.render(context)