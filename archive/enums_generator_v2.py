"""
Enums generator v2 - Using new service layer.
Maintains data-driven interface for diagram compatibility.
"""

from typing import Dict, Any, List
import json

# For direct Python usage (not from diagrams)
try:
    from files.codegen.code.services import TemplateService, MacroDefinition
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False

# For diagram usage - inline template rendering
def render_template_inline(template_content: str, context: dict) -> str:
    """Simple template rendering without external dependencies."""
    try:
        # Try to use Jinja2 if available (might be in the environment)
        from jinja2 import Template
        template = Template(template_content)
        return template.render(**context)
    except Exception as e:
        # Fallback to basic string replacement
        # This is a simplified implementation for basic templates
        import re
        result = template_content
        
        # Process nested loops by handling inner loops first
        def process_loops(text, ctx):
            # Find all for loops
            for_pattern = r'{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%}(.*?){%\s*endfor\s*%}'
            
            def replace_loop(match):
                item_name = match.group(1)
                collection_expr = match.group(2)
                loop_body = match.group(3)
                
                # Resolve collection expression (supports simple paths like enum.values)
                parts = collection_expr.split('.')
                collection = ctx
                for part in parts:
                    if isinstance(collection, dict):
                        collection = collection.get(part, [])
                    elif isinstance(collection, list) and part.isdigit():
                        collection = collection[int(part)] if int(part) < len(collection) else []
                    else:
                        collection = []
                        break
                
                if not isinstance(collection, list):
                    collection = []
                
                # Process each item
                results = []
                for item in collection:
                    # Create new context with loop variable
                    loop_ctx = ctx.copy()
                    loop_ctx[item_name] = item
                    
                    # Process loop body recursively
                    item_result = process_loops(loop_body, loop_ctx)
                    
                    # Replace variables in the processed body
                    item_result = replace_variables(item_result, loop_ctx)
                    results.append(item_result)
                
                return ''.join(results)
            
            # Process loops from innermost to outermost
            while True:
                new_text = re.sub(for_pattern, replace_loop, text, flags=re.DOTALL)
                if new_text == text:
                    break
                text = new_text
            
            return text
        
        def replace_variables(text, ctx):
            # Replace {{ variable }} and {{ variable.field }} patterns
            def replace_var(match):
                expr = match.group(1).strip()
                
                # Handle dot notation
                parts = expr.split('.')
                value = ctx
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part, '')
                    else:
                        value = ''
                        break
                
                return str(value)
            
            # Match {{ ... }} patterns
            var_pattern = r'{{\s*([^}]+)\s*}}'
            return re.sub(var_pattern, replace_var, text)
        
        # Process the template
        result = process_loops(result, context)
        result = replace_variables(result, context)
        
        return result
    except Exception as e:
        # Last resort - return template as-is
        return template_content


# Service-based generation (for direct Python usage)
def generate_enums_with_services(template_content: str, enums_data: List[dict]) -> str:
    """Generate using the new service layer - for Python imports only."""
    if not SERVICES_AVAILABLE:
        # Fallback to inline rendering
        return render_template_inline(template_content, {'enums': enums_data})
    
    # Use the new template service
    template_service = TemplateService()
    
    # Register enum-specific macros if needed
    template_service.register_macro(MacroDefinition(
        name='enum_value',
        template='{{ name }}{% if description %} = "{{ description }}"{% endif %}',
        params=['name', 'description'],
        description='Generate enum value with optional description'
    ))
    
    # Render with all the shared filters and macros
    return template_service.render_string(template_content, enums=enums_data)


# Data-driven interface for diagram nodes
def generate_enums(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate enum definitions - called by 'Generate Enums' node.
    Maintains simple data interface for diagram compatibility.
    
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
    
    # Use inline rendering for diagram execution (no external dependencies)
    generated_code = render_template_inline(template_content, {'enums': enums_data})
    
    return {
        'generated_code': generated_code,
        'filename': 'enums.py'
    }


# Utility function for pre-processing (outside diagram execution)
def prepare_enums_data(typescript_ast: dict) -> List[dict]:
    """
    Pre-process TypeScript AST to extract enum data.
    This runs OUTSIDE of diagram execution and can use services.
    """
    enums = []
    
    # Extract enums from AST
    for item in typescript_ast.get('enums', []):
        enum_data = {
            'name': item.get('name', ''),
            'values': item.get('values', []),
            'description': item.get('description', '')
        }
        enums.append(enum_data)
    
    return enums


# Backward compatibility alias
main = generate_enums