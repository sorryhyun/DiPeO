"""Pure generator for TypeScript node models."""
from typing import Dict, Any
from files.codegen.code.shared.template_env import create_template_env
from files.codegen.code.frontend.utils.typescript_mapper import (
    map_to_typescript_type,
    calculate_typescript_imports,
    get_typescript_default,
    get_zod_schema
)


def generate_typescript_model(spec_data: Dict[str, Any], template_content: str) -> str:
    """
    Pure function: Generate TypeScript model from spec and template.
    
    Args:
        spec_data: Node specification data
        template_content: Jinja2 template content
        
    Returns:
        Generated TypeScript code
    """
    env = create_template_env()
    
    # Get node type from spec
    node_type = spec_data.get('nodeType', spec_data.get('type', 'unknown'))
    
    # Transform spec for TypeScript
    ts_spec = {
        **spec_data,
        'nodeType': node_type,
        'imports': calculate_typescript_imports(spec_data),
        'type_mappings': {},
        'default_values': {},
        'zod_schemas': {},
        'interface_name': f"{node_type.title().replace('_', '')}Node",
    }
    
    # Process each field
    for field in spec_data.get('fields', []):
        field_name = field['name']
        
        # Type mapping
        ts_spec['type_mappings'][field_name] = map_to_typescript_type(field.get('type', 'string'))
        
        # Default values
        ts_spec['default_values'][field_name] = get_typescript_default(field)
        
        # Zod schemas for validation
        ts_spec['zod_schemas'][field_name] = get_zod_schema(field)
    
    # Separate required and optional fields
    ts_spec['required_fields'] = [
        field for field in spec_data.get('fields', [])
        if field.get('required', False)
    ]
    ts_spec['optional_fields'] = [
        field for field in spec_data.get('fields', [])
        if not field.get('required', False)
    ]
    
    template = env.from_string(template_content)
    return template.render(ts_spec)


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - spec_data: Node specification
            - template_content: Template string (legacy)
            - templates: Dictionary of templates (new format)
            
    Returns:
        Dictionary with:
            - generated_code: The generated TypeScript code
            - filename: Suggested filename for the output
    """
    spec_data = inputs.get('spec_data', {})
    
    # Handle both legacy and new template formats
    template_content = ''
    if 'templates' in inputs and isinstance(inputs['templates'], dict):
        # New format: find the typescript_model.j2 template
        for filepath, content in inputs['templates'].items():
            if filepath.endswith('typescript_model.j2'):
                template_content = content
                break
    else:
        # Legacy format
        template_content = inputs.get('template_content', '')
    
    if not spec_data:
        raise ValueError("spec_data is required")
    if not template_content:
        raise ValueError("template_content is required")
    
    generated_code = generate_typescript_model(spec_data, template_content)
    
    # Generate filename from node type
    node_type = spec_data.get('nodeType', spec_data.get('type', 'unknown'))
    node_name = node_type.title().replace('_', '')
    filename = f"{node_name}Node.ts"
    
    return {
        'generated_code': generated_code,
        'filename': filename,
        'node_type': node_type
    }