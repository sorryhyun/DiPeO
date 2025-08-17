#!/usr/bin/env python3
"""Fix all remaining dipeo.core imports to use core.bak or domain."""

import os
import re
from pathlib import Path

# Map of old imports to new imports
IMPORT_MAPPINGS = {
    # Constants imports
    "from dipeo.domain.constants import": "from dipeo.domain.constants import",
    "from dipeo.domain.base.exceptions import ValidationError": "from dipeo.domain.base.exceptions import ValidationError",
    "from dipeo.domain.base.exceptions import ServiceError": "from dipeo.domain.base.exceptions import ServiceError",
    
    # Config imports (these stay in core.bak for now)
    "from dipeo.core.bak.config import": "from dipeo.core.bak.config import",
    "from dipeo.core.bak.events import": "from dipeo.core.bak.events import",
    "from dipeo.core.bak.ports import": "from dipeo.core.bak.ports import",
    "from dipeo.core.bak.ports.": "from dipeo.core.bak.ports.",
    
    # Execution imports
    "from dipeo.core.bak.execution import": "from dipeo.core.bak.execution import",
    "from dipeo.core.bak.execution.": "from dipeo.core.bak.execution.",
    
    # Resolution imports
    "from dipeo.core.bak.resolution import": "from dipeo.core.bak.resolution import",
    "from dipeo.core.bak.resolution.": "from dipeo.core.bak.resolution.",
}

def fix_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)
        
        if content != original_content:
            file_path.write_text(content)
            print(f"Fixed: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all Python files in the project."""
    project_root = Path("/home/soryhyun/DiPeO")
    
    # Find all Python files
    python_files = list(project_root.glob("**/*.py"))
    
    # Exclude some directories
    exclude_dirs = ["core.bak", "scripts", ".venv", "node_modules", "__pycache__"]
    python_files = [
        f for f in python_files 
        if not any(excluded in f.parts for excluded in exclude_dirs)
    ]
    
    fixed_count = 0
    for file_path in python_files:
        if fix_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files out of {len(python_files)} checked.")

if __name__ == "__main__":
    main()