#!/usr/bin/env python3
"""Script to update imports in remaining src files that aren't in dipeo_server."""

import re
import sys
from pathlib import Path
from typing import Set, Tuple

# These files in the original src should continue to work via compatibility shims
# No need to update imports here as the shims handle it

def find_files_to_update(base_dir: Path) -> list[Path]:
    """Find Python files that need import updates."""
    files_to_update = []
    
    # Find all Python files in apps/server but exclude dipeo_server directory
    server_dir = base_dir / "apps" / "server"
    
    for py_file in server_dir.rglob("*.py"):
        # Skip files in dipeo_server (already updated)
        if "dipeo_server" in str(py_file):
            continue
            
        # Skip generated files
        if "__generated__" in str(py_file):
            continue
            
        # Skip migration scripts
        if "scripts" in str(py_file):
            continue
            
        files_to_update.append(py_file)
    
    return files_to_update

def check_imports(file_path: Path) -> Set[str]:
    """Check if a file has imports that need updating."""
    try:
        content = file_path.read_text()
        imports = set()
        
        # Find imports from src.common or src.domains
        patterns = [
            r'from src\.common',
            r'from src\.domains',
            r'import src\.common',
            r'import src\.domains',
        ]
        
        for pattern in patterns:
            if re.search(pattern, content):
                imports.add(pattern)
        
        return imports
        
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return set()

def main():
    """Main entry point."""
    base_dir = Path(__file__).parent.parent.parent.parent  # Go up to DiPeO root
    
    if not base_dir.exists():
        print(f"❌ Base directory not found: {base_dir}")
        sys.exit(1)
    
    print(f"🔍 Checking for files that still use old import paths...\n")
    
    files_to_update = find_files_to_update(base_dir)
    print(f"Found {len(files_to_update)} Python files to check\n")
    
    files_with_old_imports = []
    
    for py_file in sorted(files_to_update):
        imports = check_imports(py_file)
        if imports:
            files_with_old_imports.append((py_file, imports))
    
    if files_with_old_imports:
        print(f"📋 Files still using old imports ({len(files_with_old_imports)}):\n")
        for file_path, imports in files_with_old_imports:
            rel_path = file_path.relative_to(base_dir)
            print(f"  • {rel_path}")
            for imp in sorted(imports):
                print(f"    - Contains: {imp}")
    else:
        print("✅ No files found with old imports outside dipeo_server")
    
    print("\n💡 Note: These files will continue to work via compatibility shims")
    print("   The shims in src/__init__.py provide backward compatibility")

if __name__ == "__main__":
    main()