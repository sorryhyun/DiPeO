"""Pure generator for frontend field configuration."""
from typing import Dict, Any, List
from files.codegen.code.shared.template_env import create_template_env
from files.codegen.code.shared.filters import camel_case, pascal_case
from files.codegen.code.frontend.utils.react_helpers import (
    get_field_component,
    get_field_props,
    group_fields_for_ui
)
from files.codegen.code.frontend.utils.typescript_mapper import map_to_typescript_type


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
    
    # Pass fields directly to template with minimal transformation
    # Let the template handle the formatting
    field_configs = []
    for field in fields:
        # Keep the original field structure
        field_config = dict(field)  # Create a copy
        
        # Add any computed properties that aren't in the original
        field_config['label'] = field.get('displayName', field.get('name'))
        field_config['category'] = field.get('category', 'General')
        field_config['order'] = field.get('order', 999)
        
        field_configs.append(field_config)
    
    # Sort fields by order, then by name
    field_configs.sort(key=lambda f: (f['order'], f['name']))
    
    # Get node type from spec
    node_type = spec_data.get('nodeType', spec_data.get('type', 'unknown'))
    
    # Prepare context for template
    context = {
        **spec_data,
        'nodeType': node_type,
        'nodeTypeCamel': camel_case(node_type),
        'fields': field_configs,
        'field_groups': group_fields_for_ui(field_configs),
        'config_name': f"{camel_case(node_type)}FieldConfig",
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
    try:
        spec_data = inputs.get('spec_data', {})
        template_content = inputs.get('template_content', '')
        
        if not spec_data:
            raise ValueError("spec_data is required")
        if not template_content:
            raise ValueError("template_content is required")
        
        generated_code = generate_field_config(spec_data, template_content)
        
        # Generate filename from node type
        node_type = spec_data.get('nodeType', spec_data.get('type', 'unknown'))
        node_name = pascal_case(node_type)
        filename = f"{node_name}Fields.ts"
        
        return {
            'generated_code': generated_code,
            'filename': filename,
            'node_type': node_type
        }
    except Exception as e:
        # Return the error as generated_code so we can see what's happening
        import traceback
        error_msg = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"[Field Config Error] {error_msg}")
        return {
            'generated_code': str(e),  # This is what gets written to the file
            'filename': 'error.ts',
            'node_type': 'error'
        }