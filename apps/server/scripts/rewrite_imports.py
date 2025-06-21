#!/usr/bin/env python3
"""Script to rewrite imports from old paths to new dipeo_server paths."""

import re
import sys
from pathlib import Path
from typing import Set, Tuple

# Define import mappings
IMPORT_MAPPINGS = [
    # Common to core
    (r'from src\.common\.(\w+) import', r'from dipeo_server.core.\1 import'),
    (r'from src\.common import', r'from dipeo_server.core import'),
    (r'import src\.common\.(\w+)', r'import dipeo_server.core.\1'),
    (r'import src\.common\b', r'import dipeo_server.core'),
    
    # Domains
    (r'from src\.domains\.(\w+)', r'from dipeo_server.domains.\1'),
    (r'import src\.domains\.(\w+)', r'import dipeo_server.domains.\1'),
    
    # Generated models stay the same for now
    # (r'from src\.__generated__', r'from dipeo_server.generated'),
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
    
    # Find all Python files in the dipeo_server directory
    base_dir = Path(__file__).parent.parent / "src" / "dipeo_server"
    
    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        sys.exit(1)
    
    python_files = list(base_dir.rglob("*.py"))
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