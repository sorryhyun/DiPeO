#!/usr/bin/env python3
"""Script to flatten the API structure by moving files from subdirectories."""

import os
import shutil
from pathlib import Path

def flatten_api_structure():
    """Flatten the API structure according to TODO.md specifications."""
    
    api_dir = Path(__file__).parent.parent / "src" / "dipeo_server" / "api"
    
    if not api_dir.exists():
        print(f"❌ API directory not found: {api_dir}")
        return
    
    # Subdirectories to flatten
    subdirs_to_flatten = ["mutations", "resolvers", "types"]
    
    # Move files from subdirectories to api directory
    for subdir_name in subdirs_to_flatten:
        subdir = api_dir / subdir_name
        if subdir.exists() and subdir.is_dir():
            print(f"\n📁 Processing {subdir_name}/...")
            
            # Get all Python files except __init__.py
            for file_path in subdir.glob("*.py"):
                if file_path.name == "__init__.py":
                    continue
                    
                # Determine new filename
                if subdir_name == "mutations":
                    # For mutations, add _mutation suffix
                    new_name = file_path.stem + "_mutation.py"
                elif subdir_name == "resolvers":
                    # Resolvers already have _resolver suffix, keep as is
                    new_name = file_path.name
                elif subdir_name == "types":
                    # For types, add _types suffix to avoid conflicts
                    new_name = file_path.stem + "_types.py"
                else:
                    new_name = file_path.name
                
                new_path = api_dir / new_name
                
                # Move the file
                print(f"  Moving {file_path.name} → {new_name}")
                shutil.move(str(file_path), str(new_path))
            
            # Remove the now-empty subdirectory
            try:
                shutil.rmtree(subdir)
                print(f"  ✅ Removed {subdir_name}/ directory")
            except Exception as e:
                print(f"  ⚠️  Could not remove {subdir_name}/: {e}")
    
    # Update imports in all Python files in the API directory
    print("\n🔄 Updating imports...")
    update_imports_after_flattening(api_dir)
    
    print("\n✅ API structure flattened successfully!")

def update_imports_after_flattening(api_dir: Path):
    """Update imports after flattening the structure."""
    
    import_mappings = [
        # Mutations
        (r'from \.mutations\.(\w+) import', r'from .\1_mutation import'),
        (r'from dipeo_server\.api\.mutations\.(\w+) import', r'from dipeo_server.api.\1_mutation import'),
        (r'from \.mutations import (\w+)', r'from . import \1_mutation as \1'),
        (r'from dipeo_server\.api\.mutations import', r'from dipeo_server.api import'),
        
        # Resolvers
        (r'from \.resolvers\.(\w+) import', r'from .\1 import'),
        (r'from dipeo_server\.api\.resolvers\.(\w+) import', r'from dipeo_server.api.\1 import'),
        (r'from \.resolvers import', r'from . import'),
        (r'from dipeo_server\.api\.resolvers import', r'from dipeo_server.api import'),
        
        # Types
        (r'from \.types\.(\w+) import', r'from .\1_types import'),
        (r'from dipeo_server\.api\.types\.(\w+) import', r'from dipeo_server.api.\1_types import'),
        (r'from \.types import', r'from . import'),
        (r'from dipeo_server\.api\.types import', r'from dipeo_server.api import'),
    ]
    
    # Update imports in all Python files
    for py_file in api_dir.glob("*.py"):
        try:
            content = py_file.read_text()
            original_content = content
            
            for pattern, replacement in import_mappings:
                import re
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                py_file.write_text(content)
                print(f"  Updated imports in {py_file.name}")
                
        except Exception as e:
            print(f"  ❌ Error updating {py_file.name}: {e}")

if __name__ == "__main__":
    flatten_api_structure()