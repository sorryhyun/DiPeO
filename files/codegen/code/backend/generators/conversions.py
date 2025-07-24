"""Pure generator for model conversions between TypeScript and Python."""
from typing import Dict, Any, List
from ...shared.template_env import create_template_env


def generate_conversions(pydantic_models: List[Dict[str, Any]], template_content: str) -> str:
    """
    Pure function: Generate conversion functions between TypeScript and Python models.
    
    Args:
        pydantic_models: List of Pydantic model metadata
        template_content: Jinja2 template content
        
    Returns:
        Generated Python conversion code
    """
    env = create_template_env()
    
    # Build conversion mappings
    conversions = {
        'models': [],
        'type_conversions': _build_type_conversions(),
        'imports': _calculate_conversion_imports(pydantic_models),
    }
    
    # Process each model
    for model_info in pydantic_models:
        model_name = model_info.get('class_name', '')
        node_type = model_info.get('node_type', '')
        
        conversion = {
            'model_name': model_name,
            'node_type': node_type,
            'ts_to_py_name': f"ts_{node_type}_to_py",
            'py_to_ts_name': f"py_{node_type}_to_ts",
            'fields': model_info.get('fields', []),
            'has_enums': model_info.get('has_enums', False),
            'field_mappings': _build_field_mappings(model_info),
        }
        
        conversions['models'].append(conversion)
    
    # Add utility functions
    conversions['utilities'] = _build_utility_functions()
    
    template = env.from_string(template_content)
    return template.render(conversions)


def _build_type_conversions() -> Dict[str, Dict[str, str]]:
    """Build type conversion mappings between TypeScript and Python."""
    return {
        'ts_to_py': {
            'string': 'str',
            'number': 'float',
            'boolean': 'bool',
            'any': 'Any',
            'null': 'None',
            'undefined': 'None',
            'Date': 'datetime',
            'Record<string, any>': 'Dict[str, Any]',
            'any[]': 'List[Any]',
        },
        'py_to_ts': {
            'str': 'string',
            'int': 'number',
            'float': 'number',
            'bool': 'boolean',
            'None': 'null',
            'datetime': 'string',  # ISO format
            'date': 'string',
            'Dict': 'object',
            'List': 'array',
        }
    }


def _build_field_mappings(model_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Build field-specific conversion mappings."""
    mappings = {}
    
    # This would normally read from the actual field definitions
    # For now, return a basic mapping structure
    for field_name in model_info.get('fields', []):
        mappings[field_name] = {
            'ts_name': field_name,
            'py_name': field_name.replace('-', '_'),
            'needs_conversion': field_name != field_name.replace('-', '_'),
            'type_converter': None,  # Custom converter if needed
        }
    
    return mappings


def _build_utility_functions() -> List[Dict[str, Any]]:
    """Build utility conversion functions."""
    return [
        {
            'name': 'convert_datetime',
            'description': 'Convert between ISO string and datetime',
            'code': """def convert_datetime(value: Any, to_python: bool = True) -> Any:
    if value is None:
        return None
    if to_python and isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    elif not to_python and isinstance(value, datetime):
        return value.isoformat()
    return value"""
        },
        {
            'name': 'convert_enum',
            'description': 'Convert enum values between formats',
            'code': """def convert_enum(value: Any, enum_class: Optional[type] = None) -> Any:
    if value is None:
        return None
    if enum_class and hasattr(enum_class, value):
        return getattr(enum_class, value).value
    return value"""
        },
        {
            'name': 'deep_convert',
            'description': 'Recursively convert nested structures',
            'code': """def deep_convert(obj: Any, converter_map: Dict[str, Callable]) -> Any:
    if isinstance(obj, dict):
        return {k: deep_convert(v, converter_map) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_convert(item, converter_map) for item in obj]
    elif type(obj).__name__ in converter_map:
        return converter_map[type(obj).__name__](obj)
    return obj"""
        }
    ]


def _calculate_conversion_imports(models: List[Dict[str, Any]]) -> List[str]:
    """Calculate imports needed for conversions."""
    imports = [
        "from typing import Dict, Any, List, Optional, Union, Callable",
        "from datetime import datetime, date",
        "import json",
    ]
    
    # Add model imports
    for model in models:
        model_name = model.get('class_name', '')
        node_type = model.get('node_type', '')
        if model_name and node_type:
            imports.append(f"from dipeo.diagram_generated.models.{node_type}_model import {model_name}")
    
    return sorted(list(set(imports)))


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - pydantic_models: List of Pydantic model metadata
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated conversions code
            - filename: Output filename
    """
    pydantic_models = inputs.get('pydantic_models', [])
    template_content = inputs.get('template_content', '')
    
    if not template_content:
        raise ValueError("template_content is required")
    
    generated_code = generate_conversions(pydantic_models, template_content)
    
    return {
        'generated_code': generated_code,
        'filename': '__generated_conversions__.py'
    }