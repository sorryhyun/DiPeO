#!/usr/bin/env python3
"""Script to update imports in the original src directories to use dipeo_server."""

import re
import sys
from pathlib import Path
from typing import Set, Tuple, List

# Define import mappings for src files
IMPORT_MAPPINGS = [
    # Internal references should use dipeo_server
    (r'from src\.common\.(\w+) import', r'from dipeo_server.core.\1 import'),
    (r'from src\.common import', r'from dipeo_server.core import'),
    (r'import src\.common\.(\w+)', r'import dipeo_server.core.\1'),
    (r'import src\.common\b', r'import dipeo_server.core'),
    
    # Domains
    (r'from src\.domains\.(\w+)', r'from dipeo_server.domains.\1'),
    (r'import src\.domains\.(\w+)', r'import dipeo_server.domains.\1'),
    
    # API/GraphQL
    (r'from src\.interfaces\.graphql', r'from dipeo_server.api'),
    (r'import src\.interfaces\.graphql', r'import dipeo_server.api'),
    (r'from src\.api\.', r'from dipeo_server.api.'),
]

def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped from migration."""
    # Skip test files as they may need special handling
    if 'test' in str(file_path):
        return True
    
    # Skip generated files
    if '__generated__' in str(file_path):
        return True
    
    # Skip migration scripts
    if 'scripts' in str(file_path):
        return True
    
    # Skip files already in dipeo_server
    if 'dipeo_server' in str(file_path):
        return True
    
    return False

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
    target_dirs = [d for d in sys.argv[1:] if not d.startswith('-')]
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")
    
    # Default to updating specific directories
    if not target_dirs:
        target_dirs = ['common', 'domains', 'interfaces', 'api']
    
    base_dir = Path(__file__).parent.parent / "src"
    
    all_changes = set()
    modified_count = 0
    skipped_count = 0
    
    for target in target_dirs:
        target_path = base_dir / target
        if not target_path.exists():
            continue
            
        print(f"\n📁 Processing {target} directory...")
        
        if target_path.is_file():
            python_files = [target_path]
        else:
            python_files = list(target_path.rglob("*.py"))
        
        for py_file in sorted(python_files):
            if should_skip_file(py_file):
                skipped_count += 1
                continue
                
            changes = rewrite_imports_in_file(py_file, dry_run)
            if changes:
                all_changes.update(changes)
                modified_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  - Files to modify: {modified_count}")
    print(f"  - Files skipped: {skipped_count}")
    print(f"  - Unique import changes: {len(all_changes)}")
    
    if dry_run and modified_count > 0:
        print("\n💡 Run without --dry-run to apply changes")

if __name__ == "__main__":
    main()