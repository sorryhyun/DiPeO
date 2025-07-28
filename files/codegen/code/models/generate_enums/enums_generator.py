"""
Enums generator for DiPeO.
Generates Python enum definitions from TypeScript AST data.
"""

import json
from typing import Dict, Any, List
from files.codegen.code.shared.template_env import create_template_env


# ============================================================================
# Generation Functions
# ============================================================================

def generate_enums_code(template_content: str, enums_data: List[dict]) -> str:
    """
    Generate enum definitions using template.
    
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


# ============================================================================
# Main Functions (called by diagram nodes)
# ============================================================================

def generate_enums(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate enum definitions - called by 'Generate Enums' node.
    
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
    
    generated_code = generate_enums_code(template_content, enums_data)
    
    return {
        'generated_code': generated_code,
        'filename': 'enums.py'
    }


# Backward compatibility alias
main = generate_enums