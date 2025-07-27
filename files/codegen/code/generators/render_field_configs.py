"""Generate field configurations code from template."""
import traceback
from datetime import datetime
from typing import Any, Dict

from jinja2 import Template, StrictUndefined


def render_field_configs(inputs: Dict[str, Any]) -> str:
    """
    Render field configurations using Jinja2 template.
    
    Args:
        inputs: Dictionary containing template_content and default data
        
    Returns:
        Rendered template string or error message
    """
    # Get template content
    template_content = inputs.get('template_content', '')
    
    # Get prepared data
    template_data = inputs.get('default', {})
    
    print(f"Template data keys: {list(template_data.keys())}")
    print(f"Node configs count: {len(template_data.get('node_configs', []))}")
    
    try:
        # Render template
        jinja_template = Template(template_content, undefined=StrictUndefined)
        rendered = jinja_template.render(**template_data)
        
        print(f"Successfully rendered template, length: {len(rendered)}")
        
        # DB write node expects the string directly as 'default' input
        return rendered
    except Exception as e:
        print(f"Template rendering error: {e}")
        print(traceback.format_exc())
        # Return error as content so we can see it
        return f"/* Template rendering error: {e} */\n"