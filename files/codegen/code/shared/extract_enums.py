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
    # Get the parsed AST
    ast = ast_data.get('ast', {})
    
    # Initialize result
    enums = []
    
    # Look for exported enums in the AST
    body = ast.get('body', [])
    
    for statement in body:
        if statement.get('type') == 'ExportNamedDeclaration':
            declaration = statement.get('declaration', {})
            
            if declaration.get('type') == 'TSEnumDeclaration':
                id_node = declaration.get('id', {})
                
                if id_node.get('type') == 'Identifier':
                    enum_name = id_node.get('name', '')
                    
                    # Extract description from JSDoc
                    description = extract_jsdoc_description(declaration)
                    
                    # Extract enum members
                    members = declaration.get('members', [])
                    values = extract_enum_values(members)
                    
                    # Add to results
                    if enum_name and values:
                        enums.append({
                            'name': enum_name,
                            'description': description or f'{enum_name} enum values',
                            'values': values
                        })
    
    return enums


def main(inputs: dict) -> dict:
    """Main entry point for enum extraction."""
    ast_data = inputs.get('default', {})
    enums = extract_enums(ast_data)
    
    return {'enums': enums}