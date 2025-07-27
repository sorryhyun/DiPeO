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
    
    # Handle case where enums_data might be a JSON string
    if isinstance(enums_data, str):
        try:
            import ast
            # Try to parse as Python literal first (DiPeO might pass it this way)
            enums_data = ast.literal_eval(enums_data)
        except:
            try:
                enums_data = json.loads(enums_data)
            except:
                # If parsing fails, use empty list to avoid template errors
                enums_data = []
    
    if not template_content:
        raise ValueError("template_content is required")
    
    # Validate we have enums
    if not isinstance(enums_data, list):
        enums_data = []  # Use empty list to avoid template errors
    
    generated_code = generate_enums(template_content, enums_data)
    
    return {
        'generated_code': generated_code,
        'filename': 'enums.py'
    }