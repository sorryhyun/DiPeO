"""File globbing utility for code generation."""

import glob
import os


def glob_typescript_files(inputs):
    """Get all TypeScript files from source directory."""
    # Get all TypeScript files from source directory
    source_dir = inputs.get('source_dir', 'dipeo/models/src')
    # Make it absolute if it's relative
    if not os.path.isabs(source_dir):
        source_dir = os.path.join(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'), source_dir)
    
    pattern = os.path.join(source_dir, '**/*.ts')
    files = glob.glob(pattern, recursive=True)
    
    # Filter out test files and type definition files
    files = [f for f in files if not f.endswith('.test.ts') and not f.endswith('.d.ts')]
    
    print(f"Found {len(files)} TypeScript files to process")
    result = {'typescript_files': files, 'file_count': len(files)}
    # DiPeO expects a 'default' key for passing data between nodes
    result['default'] = result.copy()
    return result