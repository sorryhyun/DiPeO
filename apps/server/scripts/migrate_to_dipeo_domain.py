#!/usr/bin/env python3
"""Script to migrate imports from __generated__ models to dipeo_domain package."""

import re
import sys
from pathlib import Path
from typing import Set, Tuple

# Define import mappings for domain models
IMPORT_MAPPINGS = [
    # Generated models to dipeo_domain
    (r'from src\.__generated__ import (\w+)', r'from dipeo_domain import \1'),
    (r'from src\.__generated__\.models import', r'from dipeo_domain import'),
    (r'import src\.__generated__\.models', r'import dipeo_domain'),
    (r'import src\.__generated__', r'import dipeo_domain'),
    
    # Also handle dipeo_server.__generated__ patterns
    (r'from dipeo_server\.__generated__ import (\w+)', r'from dipeo_domain import \1'),
    (r'from dipeo_server\.__generated__\.models import', r'from dipeo_domain import'),
    (r'import dipeo_server\.__generated__\.models', r'import dipeo_domain'),
    (r'import dipeo_server\.__generated__', r'import dipeo_domain'),
]

def rewrite_imports_in_file(file_path: Path, dry_run: bool = True) -> Set[Tuple[str, str]]:
    """Rewrite imports in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        changes = set()
        
        for pattern, replacement in IMPORT_MAPPINGS:
            # Find all matches before replacing
            matches = re.finditer(pattern, content)
            for match in matches:
                old_import = match.group(0)
                new_import = re.sub(pattern, replacement, old_import)
                if old_import != new_import:
                    changes.add((old_import, new_import))
            
            # Perform replacement
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            if not dry_run:
                file_path.write_text(content)
                print(f"✅ Updated: {file_path}")
            else:
                print(f"Would update: {file_path}")
                for old, new in sorted(changes):
                    print(f"  {old} → {new}")
        
        return changes
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return set()

def main():
    """Main entry point."""
    # Parse arguments
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")
    
    # Find all Python files in the server src directory
    base_dir = Path(__file__).parent.parent / "src"
    
    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        sys.exit(1)
    
    # Get all Python files except __generated__ ones
    python_files = []
    for py_file in base_dir.rglob("*.py"):
        if "__generated__" not in str(py_file):
            python_files.append(py_file)
    
    print(f"Found {len(python_files)} Python files to process\n")
    
    all_changes = set()
    modified_count = 0
    
    for py_file in sorted(python_files):
        changes = rewrite_imports_in_file(py_file, dry_run)
        if changes:
            all_changes.update(changes)
            modified_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  - Files to modify: {modified_count}")
    print(f"  - Unique import changes: {len(all_changes)}")
    
    if dry_run and modified_count > 0:
        print("\n💡 Run without --dry-run to apply changes")

if __name__ == "__main__":
    main()