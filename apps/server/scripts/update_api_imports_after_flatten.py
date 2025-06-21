#!/usr/bin/env python3
"""Update imports throughout the codebase after flattening API structure."""

import re
from pathlib import Path

def update_api_imports():
    """Update imports after flattening the API structure."""
    
    # Get the server src directory
    src_dir = Path(__file__).parent.parent / "src"
    
    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return
    
    # Define import mappings
    import_mappings = [
        # Mutations - update to new _mutation suffix
        (r'from dipeo_server\.api\.mutations\.(\w+) import', r'from dipeo_server.api.\1_mutation import'),
        (r'from dipeo_server\.api\.mutations import (\w+)', r'from dipeo_server.api import \1_mutation as \1'),
        (r'import dipeo_server\.api\.mutations\.(\w+)', r'import dipeo_server.api.\1_mutation'),
        
        # Resolvers - no suffix change needed
        (r'from dipeo_server\.api\.resolvers\.(\w+) import', r'from dipeo_server.api.\1 import'),
        (r'from dipeo_server\.api\.resolvers import', r'from dipeo_server.api import'),
        (r'import dipeo_server\.api\.resolvers\.(\w+)', r'import dipeo_server.api.\1'),
        
        # Types - update to new _types suffix
        (r'from dipeo_server\.api\.types\.(\w+) import', r'from dipeo_server.api.\1_types import'),
        (r'from dipeo_server\.api\.types import (\w+)', r'from dipeo_server.api import \1_types as \1'),
        (r'import dipeo_server\.api\.types\.(\w+)', r'import dipeo_server.api.\1_types'),
        
        # Models - keep as is (not being flattened)
        # No changes needed for models/
    ]
    
    # Find all Python files in the src directory
    python_files = list(src_dir.rglob("*.py"))
    
    print(f"Found {len(python_files)} Python files to check")
    
    modified_count = 0
    
    for py_file in python_files:
        # Skip files in __generated__ directories
        if "__generated__" in str(py_file):
            continue
            
        try:
            content = py_file.read_text()
            original_content = content
            
            # Apply all import mappings
            for pattern, replacement in import_mappings:
                content = re.sub(pattern, replacement, content)
            
            # If content changed, write it back
            if content != original_content:
                py_file.write_text(content)
                print(f"✅ Updated: {py_file.relative_to(src_dir)}")
                modified_count += 1
                
        except Exception as e:
            print(f"❌ Error processing {py_file}: {e}")
    
    print(f"\n📊 Summary: Updated {modified_count} files")

if __name__ == "__main__":
    update_api_imports()