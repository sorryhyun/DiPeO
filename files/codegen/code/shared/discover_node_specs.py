"""
Discover node specifications by scanning the node-data directory.
"""
import os
from pathlib import Path

def discover_node_specs(inputs):
    """Discover all node specs by scanning the node-data directory."""
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    node_data_dir = base_dir / 'dipeo' / 'models' / 'src' / 'node-data'
    
    # Base AST files that are always included
    base_ast_files = [
        '.temp/diagram_ast.json',
        '.temp/execution_ast.json',
        '.temp/conversation_ast.json',
        '.temp/enums_ast.json',
        '.temp/integration_ast.json'
    ]
    
    # Discover node data files
    node_ast_files = []
    node_names = []
    
    if node_data_dir.exists():
        for file_path in node_data_dir.glob('*.data.ts'):
            if file_path.name != 'index.ts':
                # Extract node name from filename (e.g., 'api-job.data.ts' -> 'api-job')
                node_name = file_path.stem.replace('.data', '')
                node_names.append(node_name)
                
                # Generate corresponding AST cache file path
                ast_file = f'.temp/{node_name}_data_ast.json'
                node_ast_files.append(ast_file)
    
    # Sort for consistent ordering
    node_ast_files.sort()
    node_names.sort()
    
    # Combine all file paths
    all_file_paths = base_ast_files + node_ast_files
    
    print(f"Discovered {len(node_names)} node specs: {', '.join(node_names)}")
    
    return {
        'file_paths': all_file_paths,
        'base_files': base_ast_files,
        'node_files': node_ast_files,
        'node_names': node_names,
        'node_count': len(node_names)
    }

def generate_db_source_details(inputs):
    """Generate source_details list for DB node from discovered specs."""
    discovered = inputs.get('discovered_specs', {})
    file_paths = discovered.get('file_paths', [])
    
    # Return just the file paths for DB node's source_details
    return file_paths