"""Pure generator for Pydantic models."""
from typing import Dict, Any
from files.codegen.code.shared.template_env import create_template_env
from files.codegen.code.backend.utils.python_mapper import (
    map_to_python_type,
    calculate_python_imports,
    get_pydantic_field,
    pythonize_name
)
from files.codegen.code.backend.utils.pydantic_helpers import (
    build_validators,
    build_model_config,
    generate_enum_classes
)


def generate_pydantic_model(spec_data: Dict[str, Any], template_content: str) -> str:
    """
    Pure function: Generate Pydantic model from spec and template.
    
    Args:
        spec_data: Node specification data
        template_content: Jinja2 template content
        
    Returns:
        Generated Python Pydantic model code
    """
    env = create_template_env()
    
    # Transform spec for Python/Pydantic
    py_spec = {
        **spec_data,
        'imports': calculate_python_imports(spec_data),
        'type_mappings': {},
        'field_definitions': {},
        'validators': build_validators(spec_data),
        'model_config': build_model_config(spec_data),
        'enum_classes': generate_enum_classes(spec_data),
        'class_name': f"{spec_data.get('nodeType', 'unknown').title().replace('_', '')}Node",
    }
    
    # Process each field
    for field in spec_data.get('fields', []):
        original_name = field['name']
        python_name = pythonize_name(original_name)
        
        # Store both original and pythonized names
        field['python_name'] = python_name
        field['needs_alias'] = python_name != original_name
        
        # Type mapping
        py_spec['type_mappings'][python_name] = map_to_python_type(field.get('type', 'string'))
        
        # Field definition with Pydantic Field()
        py_spec['field_definitions'][python_name] = get_pydantic_field(field)
    
    # Separate required and optional fields
    py_spec['required_fields'] = [
        field for field in spec_data.get('fields', [])
        if field.get('required', False)
    ]
    py_spec['optional_fields'] = [
        field for field in spec_data.get('fields', [])
        if not field.get('required', False)
    ]
    
    # Add any custom methods
    py_spec['custom_methods'] = spec_data.get('methods', [])
    
    # Create context with both original spec and enhanced data
    context = {
        **spec_data,  # All original fields (nodeType, displayName, fields, etc.)
        **py_spec,    # Enhanced Python-specific data
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
            - generated_code: The generated Python code
            - filename: Suggested filename for the output
            - metadata: Additional metadata about the generated model
    """
    try:
        spec_data = inputs.get('spec_data', {})
        template_content = inputs.get('template_content', '')
        
        if not spec_data:
            raise ValueError("spec_data is required")
        if not template_content:
            raise ValueError("template_content is required")
        
        generated_code = generate_pydantic_model(spec_data, template_content)
        
        # Generate filename from node type
        node_type = spec_data.get('nodeType', 'unknown')
        filename = f"{node_type}_model.py"
        
        # Extract metadata for use by other generators
        metadata = {
            'node_type': node_type,
            'class_name': f"{node_type.title().replace('_', '')}Node",
            'fields': [field['name'] for field in spec_data.get('fields', [])],
            'has_validators': len(spec_data.get('validators', [])) > 0,
            'has_enums': any(field.get('enum') for field in spec_data.get('fields', []))
        }
        
        return {
            'generated_code': generated_code,
            'filename': filename,
            'metadata': metadata
        }
    except Exception as e:
        # Return the error in the expected format for debugging
        import traceback
        return {
            'generated_code': f"# ERROR in pydantic_model.py:\n# {str(e)}\n# Traceback:\n# {traceback.format_exc()}",
            'filename': 'error.py',
            'metadata': {'error': str(e)}
        }


def generate_batch(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate multiple Pydantic models in batch.
    
    Args:
        inputs: List of generation tasks, each containing:
            - node_type: The node type
            - output_path: Where to write the file
            - spec_data: Node specification
            - template_path: Path to template file
            
    Returns:
        List of results with generated files and metadata
    """
    import os
    
    tasks = inputs if isinstance(inputs, list) else []
    results = []
    base_dir = os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO')
    
    for task in tasks:
        try:
            # Read template
            template_path = os.path.join(base_dir, task['template_path'])
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Generate code
            spec_data = task['spec_data']
            generated_code = generate_pydantic_model(spec_data, template_content)
            
            # Write output file
            output_path = os.path.join(base_dir, task['output_path'])
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(generated_code)
            
            # Add to results
            results.append({
                'node_type': task['node_type'],
                'output_path': task['output_path'],
                'status': 'generated',
                'metadata': {
                    'class_name': f"{task['node_type'].title().replace('_', '')}Node",
                    'fields': [field['name'] for field in spec_data.get('fields', [])]
                }
            })
            
        except Exception as e:
            results.append({
                'node_type': task.get('node_type', 'unknown'),
                'output_path': task.get('output_path', ''),
                'status': 'error',
                'error': str(e)
            })
    
    return results