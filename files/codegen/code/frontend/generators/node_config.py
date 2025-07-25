"""Pure generator for frontend node configuration."""
from typing import Dict, Any
from files.codegen.code.shared.template_env import create_template_env
from files.codegen.code.shared.spec_loader import group_fields_by_category
from files.codegen.code.shared.filters import camel_case, pascal_case
from files.codegen.code.frontend.utils.react_helpers import (
    get_field_component,
    get_field_props,
    get_icon_for_node_type,
    get_node_color,
    calculate_default_form_values
)


def generate_node_config(spec_data: Dict[str, Any], template_content: str) -> str:
    """
    Pure function: Generate frontend node configuration from spec and template.
    
    Args:
        spec_data: Node specification data
        template_content: Jinja2 template content
        
    Returns:
        Generated TypeScript configuration code
    """
    env = create_template_env()
    
    # Get node type from spec
    node_type = spec_data.get('nodeType', spec_data.get('type', 'unknown'))
    
    # Add UI-specific transformations
    config_spec = {
        **spec_data,
        'nodeType': node_type,
        'nodeTypeCamel': camel_case(node_type),
        'nodeTypePascal': pascal_case(node_type),
        'field_groups': group_fields_by_category(spec_data),
        'default_values': calculate_default_form_values(spec_data.get('fields', [])),
        'icon': spec_data.get('icon', '🔧'),
        'color': spec_data.get('color', '#6366f1'),
        'config_name': f"{camel_case(node_type)}NodeConfig",
    }
    
    # Process fields for UI components
    for field in config_spec.get('fields', []):
        field['component'] = get_field_component(field)
        field['props'] = get_field_props(field)
    
    # Add handle configuration - use the actual handles from spec
    if 'handles' not in spec_data:
        config_spec['handles'] = {
            'inputs': [{'id': 'input', 'label': ''}],
            'outputs': [{'id': 'output', 'label': ''}],
        }
    
    # Add behavior configuration
    config_spec['behavior'] = {
        'deletable': spec_data.get('deletable', True),
        'copyable': spec_data.get('copyable', True),
        'runnable': spec_data.get('runnable', True),
        'configurable': len(spec_data.get('fields', [])) > 0,
    }
    
    template = env.from_string(template_content)
    return template.render(config_spec)


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - spec_data: Node specification
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated configuration code
            - filename: Suggested filename for the output
    """
    spec_data = inputs.get('spec_data', {})
    template_content = inputs.get('template_content', '')
    
    if not spec_data:
        raise ValueError("spec_data is required")
    if not template_content:
        raise ValueError("template_content is required")
    
    generated_code = generate_node_config(spec_data, template_content)
    
    # Generate filename from node type
    node_type = spec_data.get('nodeType', spec_data.get('type', 'unknown'))
    node_name = pascal_case(node_type)
    filename = f"{node_name}Config.ts"
    
    return {
        'generated_code': generated_code,
        'filename': filename,
        'node_type': node_type
    }