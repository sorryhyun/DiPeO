"""Simplified template rendering - replaces all the wrapper functions."""

import json
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
import re

def render_and_save(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic template rendering function that replaces all the specific wrapper functions.
    
    Expected inputs:
    - template: template filename (e.g. 'typescript_model.j2')
    - output_path: where to save the rendered output
    - spec_data: data to pass to the template
    """
    template_name = inputs.get('template')
    output_path = inputs.get('output_path')
    spec_data = inputs.get('spec_data', {})
    
    if isinstance(spec_data, str):
        spec_data = json.loads(spec_data)
    
    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader('files/codegen/templates'),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add essential filters only
    env.filters['camelCase'] = lambda text: camel_case(text)
    env.filters['PascalCase'] = lambda text: pascal_case(text)
    env.filters['snake_case'] = lambda text: snake_case(text)
    
    # Render template
    template = env.get_template(template_name)
    content = template.render(**spec_data)
    
    # Write output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)
    
    return {
        'success': True,
        'output_path': str(output_path),
        'message': f"Rendered {template_name} to {output_path}"
    }

# Essential case conversion functions only
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