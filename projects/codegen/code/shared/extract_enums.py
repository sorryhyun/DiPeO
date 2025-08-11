"""Extract enum definitions from TypeScript AST."""

from typing import Dict, Any, List


def extract_enum_values(members: List[dict]) -> List[dict]:
    """Extract values from enum members."""
    values = []
    for member in members:
        if member.get('type') == 'EnumMember':
            id_node = member.get('id', {})
            init_node = member.get('initializer', {})
            
            # Get the enum member name
            if id_node.get('type') == 'Identifier':
                name = id_node.get('name', '')
                
                # Get the enum member value
                value = name  # Default to name if no initializer
                if init_node and init_node.get('type') == 'Literal':
                    value = init_node.get('value', name)
                
                values.append({
                    'name': name.lower(),  # Convert to lowercase for Python
                    'value': value
                })
    return values


def extract_jsdoc_description(node: dict) -> str:
    """Extract description from JSDoc comments."""
    leading_comments = node.get('leadingComments', [])
    for comment in leading_comments:
        if comment.get('type') == 'CommentBlock':
            text = comment.get('value', '').strip()
            # Remove JSDoc markers and extract description
            lines = text.split('\n')
            description_lines = []
            for line in lines:
                line = line.strip().lstrip('*').strip()
                if line and not line.startswith('@'):
                    description_lines.append(line)
            if description_lines:
                return ' '.join(description_lines)
    return ''


def extract_enums(ast_data: dict) -> List[dict]:
    """Extract enum definitions from TypeScript AST data."""
    # Handle case where ast_data might be a list (the enums array directly)
    if isinstance(ast_data, list):
        enums_from_ast = ast_data
    else:
        # The typescript_ast node returns enums directly
        enums_from_ast = ast_data.get('enums', [])
    
    # Initialize result
    enums = []
    
    # Process each enum
    for enum in enums_from_ast:
        enum_name = enum.get('name', '')
        description = enum.get('jsDoc', '') or f'{enum_name} enum values'
        members = enum.get('members', [])
        
        # Extract values
        values = []
        for member in members:
            member_name = member.get('name', '')
            member_value = member.get('value', member_name)
            
            if member_name:
                values.append({
                    'name': member_name,
                    'value': member_value,
                    'python_name': member_name  # Keep original case for Python
                })
        
        # Add to results
        if enum_name and values:
            enums.append({
                'name': enum_name,
                'description': description,
                'values': values
            })
    
    return enums


def main(inputs: dict) -> dict:
    """Main entry point for enum extraction."""
    ast_data = inputs.get('default', {})
    # Handle multiple files loaded with glob
    all_enums = []
    
    if isinstance(ast_data, dict) and all(isinstance(k, str) and k.endswith('.json') for k in ast_data.keys()):
        # Multiple files from glob operation
        for file_path, file_content in ast_data.items():
            # Skip invalid entries (strings or None)
            if not isinstance(file_content, dict):
                print(f"  Skipping {file_path}: Invalid content type {type(file_content).__name__}")
                continue
                
            file_enums = extract_enums(file_content)
            all_enums.extend(file_enums)
    else:
        # Single file or direct data
        all_enums = extract_enums(ast_data)

    # Return directly as dict with 'enums' key
    # The template_job will receive this via the labeled connection
    return {'enums': all_enums}