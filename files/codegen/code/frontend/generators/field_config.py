"""Pure generator for frontend field configuration."""
from typing import Dict, Any, List
from ...shared.template_env import create_template_env
from ..utils.react_helpers import (
    get_field_component,
    get_field_props,
    group_fields_for_ui
)
from ..utils.typescript_mapper import map_to_typescript_type


def generate_field_config(spec_data: Dict[str, Any], template_content: str) -> str:
    """
    Pure function: Generate frontend field configuration from spec and template.
    
    Args:
        spec_data: Node specification data
        template_content: Jinja2 template content
        
    Returns:
        Generated TypeScript field configuration code
    """
    env = create_template_env()
    
    fields = spec_data.get('fields', [])
    
    # Transform fields for frontend use
    field_configs = []
    for field in fields:
        field_config = {
            'name': field.get('name'),
            'label': field.get('displayName', field.get('name')),
            'type': map_to_typescript_type(field.get('type', 'string')),
            'component': get_field_component(field),
            'props': get_field_props(field),
            'required': field.get('required', False),
            'description': field.get('description', ''),
            'category': field.get('category', 'General'),
            'order': field.get('order', 999),
        }
        
        # Add validation rules if present
        validation_rules = []
        if field.get('required'):
            validation_rules.append({'type': 'required', 'message': f"{field_config['label']} is required"})
        if 'min' in field:
            validation_rules.append({'type': 'min', 'value': field['min'], 'message': f"Minimum value is {field['min']}"})
        if 'max' in field:
            validation_rules.append({'type': 'max', 'value': field['max'], 'message': f"Maximum value is {field['max']}"})
        if 'pattern' in field:
            validation_rules.append({'type': 'pattern', 'value': field['pattern'], 'message': 'Invalid format'})
        
        if validation_rules:
            field_config['validation'] = validation_rules
        
        field_configs.append(field_config)
    
    # Sort fields by order, then by name
    field_configs.sort(key=lambda f: (f['order'], f['name']))
    
    # Prepare context for template
    context = {
        **spec_data,
        'fields': field_configs,
        'field_groups': group_fields_for_ui(field_configs),
        'config_name': f"{spec_data.get('type', 'unknown').replace('_', '')}FieldConfig",
        'has_validation': any(f.get('validation') for f in field_configs),
        'has_categories': len(set(f['category'] for f in field_configs)) > 1,
    }
    
    template = env.from_string(template_content)
    return template.render(context)


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - spec_data: Node specification
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated field configuration code
            - filename: Suggested filename for the output
    """
    spec_data = inputs.get('spec_data', {})
    template_content = inputs.get('template_content', '')
    
    if not spec_data:
        raise ValueError("spec_data is required")
    if not template_content:
        raise ValueError("template_content is required")
    
    generated_code = generate_field_config(spec_data, template_content)
    
    # Generate filename from node type
    node_type = spec_data.get('type', 'unknown')
    filename = f"{node_type}Fields.ts"
    
    return {
        'generated_code': generated_code,
        'filename': filename,
        'node_type': node_type
    }