"""Generate conversions code from template and NODE_TYPE_MAP data."""

from datetime import datetime
from jinja2 import Template, StrictUndefined


def generate_conversions(template_content: str, node_type_map: dict) -> str:
    """Generate conversions code using Jinja2 template."""
    # Prepare template variables
    template_vars = {
        'node_type_map': node_type_map,
        'now': datetime.now().isoformat()
    }
    
    # Render template
    jinja_template = Template(template_content, undefined=StrictUndefined)
    rendered = jinja_template.render(**template_vars)
    
    return rendered


def main(inputs: dict) -> dict:
    """Main entry point for conversions generation."""
    # Get template content
    template_content = inputs.get('template_content', '')
    
    # Get node type map from extractor
    data = inputs.get('data', {})
    node_type_map = data.get('node_type_map', {})
    
    generated_code = generate_conversions(template_content, node_type_map)
    
    return {'generated_code': generated_code}