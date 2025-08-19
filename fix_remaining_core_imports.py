#!/usr/bin/env python3
"""Fix remaining core.bak imports to use compat_imports or domain layer."""

import os
import re
from pathlib import Path

# Define replacements
REPLACEMENTS = [
    # ExecutionContext
    (r'from dipeo\.core\.bak\.execution\.execution_context import ExecutionContext',
     'from dipeo.domain.execution.execution_context import ExecutionContext'),
    
    # Core imports to compat_imports
    (r'from dipeo\.core\.bak\.ports import (\w+)',
     r'from dipeo.application.migration.compat_imports import \1'),
    
    # Core events
    (r'from dipeo\.core\.bak\.events import',
     'from dipeo.domain.events import'),
    
    # Core exceptions
    (r'from dipeo\.core\.exceptions import',
     'from dipeo.domain.base.exceptions import'),
    
    # Core base
    (r'from dipeo\.core\.base import',
     'from dipeo.domain.base import'),
    
    # Core execution
    (r'from dipeo\.core\.execution import',
     'from dipeo.domain.execution import'),
    
    # Generic core imports
    (r'from dipeo\.core import',
     'from dipeo.domain import'),
]

def fix_file(file_path: Path):
    """Fix imports in a single file."""
    try:
        content = file_path.read_text()
        original = content
        
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        if content != original:
            file_path.write_text(content)
            print(f"Fixed: {file_path}")
            return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    return False

def main():
    """Fix all Python files with core imports."""
    base_dir = Path("/home/soryhyun/DiPeO")
    
    # Find all Python files that might have core imports
    python_files = []
    for pattern in ["dipeo/application/**/*.py", "dipeo/infrastructure/**/*.py", "apps/**/*.py"]:
        python_files.extend(base_dir.glob(pattern))
    
    fixed_count = 0
    for file_path in python_files:
        if fix_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()