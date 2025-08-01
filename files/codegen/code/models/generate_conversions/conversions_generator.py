"""
Conversions generator for DiPeO.
Consolidates NODE_TYPE_MAP extraction and conversions code generation.
"""

import re
from datetime import datetime
from typing import Dict
from jinja2 import Template, StrictUndefined


# ============================================================================
# Extraction Functions
# ============================================================================

def extract_node_type_map_from_ast(ast_data: dict, ts_content: str) -> dict:
    """Extract NODE_TYPE_MAP entries from TypeScript AST or source content."""
    constants = ast_data.get('constants', [])
    
    # Process constants
    
    # Find NODE_TYPE_MAP constant
    node_type_map = {}
    for const in constants:
        if const.get('name') == 'NODE_TYPE_MAP':
            # The initializer should contain the object literal
            initializer = const.get('value', const.get('initializer', ''))
            
            # Extract key-value pairs using regex
            pattern = r"'([^']+)':\s*NodeType\.([A-Z_]+)"
            matches = re.findall(pattern, str(initializer))
            for key, value in matches:
                node_type_map[key] = value
            break
    
    # If regex didn't work, try parsing the raw TypeScript
    if not node_type_map:
        # Try parsing from raw TypeScript
        if ts_content:
            # Find NODE_TYPE_MAP definition
            map_match = re.search(r'export\s+const\s+NODE_TYPE_MAP[^{]*\{([^}]+)\}', ts_content, re.DOTALL)
            if map_match:
                map_content = map_match.group(1)
                pattern = r"'([^']+)':\s*NodeType\.([A-Z_]+)"
                matches = re.findall(pattern, map_content)
                for key, value in matches:
                    node_type_map[key] = value
    
    print(f"Found {len(node_type_map)} node type mappings")
    
    return {
        'node_type_map': node_type_map,
        'entries_count': len(node_type_map)
    }


# ============================================================================
# Generation Functions
# ============================================================================

def generate_conversions_code(template_content: str, node_type_map: dict) -> str:
    """Generate conversions code using Jinja2 template."""
    # Prepare template variables
    template_vars = {
        'node_type_map': node_type_map,
        'now': datetime.now().isoformat()
    }
    
    # Render template
    jinja_template = Template(template_content, undefined=StrictUndefined)
    rendered = jinja_template.render(**template_vars)
    
    return rendered


# ============================================================================
# Main Functions (called by diagram nodes)
# ============================================================================

def extract_node_type_map(inputs: dict) -> dict:
    """Extract NODE_TYPE_MAP from TypeScript - called by 'Extract NODE_TYPE_MAP' node."""
    ast_data = inputs.get('ast_data', {})
    ts_content = inputs.get('source', '')
    
    return extract_node_type_map_from_ast(ast_data, ts_content)


def generate_conversions(inputs: dict) -> dict:
    """Generate conversions code - called by 'Generate Conversions Code' node."""
    # Get template content
    template_content = inputs.get('template_content', '')
    
    # Get node type map from extractor
    data = inputs.get('data', {})
    node_type_map = data.get('node_type_map', {})
    
    generated_code = generate_conversions_code(template_content, node_type_map)
    
    return {'generated_code': generated_code}


# Backward compatibility aliases
main = extract_node_type_map  # Default to extraction for old references