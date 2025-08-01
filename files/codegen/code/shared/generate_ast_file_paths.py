"""
Generate AST file paths dynamically from manifest.
"""

def generate_ast_file_paths(inputs):
    """Generate AST file paths from manifest data."""
    manifest = inputs.get('manifest', {})
    
    # Base AST files that are always included
    base_ast_files = [
        '.temp/diagram_ast.json',
        '.temp/execution_ast.json',
        '.temp/conversation_ast.json',
        '.temp/enums_ast.json',
        '.temp/integration_ast.json'
    ]
    
    # Generate node data AST file paths from manifest
    node_ast_files = []
    nodes = manifest.get('nodes', [])
    
    for node_name in nodes:
        # Convert underscores to hyphens for file naming
        file_node_name = node_name.replace('_', '-')
        ast_file = f'.temp/{file_node_name}_data_ast.json'
        node_ast_files.append(ast_file)
    
    # Combine all file paths
    all_file_paths = base_ast_files + node_ast_files
    
    return {
        'file_paths': all_file_paths,
        'base_files': base_ast_files,
        'node_files': node_ast_files,
        'node_count': len(nodes)
    }