"""Pure generator for enum definitions."""
from typing import Dict, Any, List
from files.codegen.code.shared.template_env import create_template_env
import json
import os


def generate_enums(template_content: str, enums_data: List[dict]) -> str:
    """
    Pure function: Generate enum definitions.
    
    Args:
        template_content: Jinja2 template content
        enums_data: List of enum definitions extracted from TypeScript
        
    Returns:
        Generated Python enum code
    """
    env = create_template_env()
    
    # Render template with dynamic enum data
    template = env.from_string(template_content)
    return template.render(enums=enums_data)


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - template_content: Template string
            - enums_data: List of enum definitions extracted from TypeScript
            
    Returns:
        Dictionary with:
            - generated_code: The generated enums code
            - filename: Output filename
    """
    template_content = inputs.get('template_content', '')
    enums_data = inputs.get('enums_data', [])
    
    if not template_content:
        raise ValueError("template_content is required")
    
    if not enums_data:
        raise ValueError("enums_data is required")
    
    generated_code = generate_enums(template_content, enums_data)
    
    return {
        'generated_code': generated_code,
        'filename': 'enums.py'
    }