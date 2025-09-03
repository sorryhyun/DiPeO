#!/usr/bin/env python3
"""Pre-commit hook to check for direct diagram internal access in application layer."""

import argparse
import re
import sys
from pathlib import Path
from typing import List

# Patterns that indicate direct access to diagram internals
FORBIDDEN_PATTERNS = [
    (r'\bdiagram\.edges\b(?! if edge)', 'Direct access to diagram.edges - use diagram.get_incoming_edges() or diagram.get_outgoing_edges()'),
    (r'\bdiagram\.nodes\b(?!_by_type)(?!\s*$)(?!\s*\))(?!\s*or\s)', 'Direct access to diagram.nodes - use diagram.get_nodes_by_type() or specific query methods'),
    (r'for\s+\w+\s+in\s+diagram\.edges', 'Iterating over diagram.edges - use diagram.get_incoming_edges() or diagram.get_outgoing_edges()'),
    (r'for\s+\w+\s+in\s+(?!.*get_nodes_by_type).*diagram\.nodes', 'Iterating over diagram.nodes - use diagram.get_nodes_by_type() or diagram.get_start_nodes()'),
    (r'\[.*for.*in\s+diagram\.edges.*\]', 'List comprehension over diagram.edges - use query methods'),
    (r'\[.*for.*in\s+(?!.*get_nodes_by_type).*diagram\.nodes.*\]', 'List comprehension over diagram.nodes - use query methods'),
]

# Allowed patterns (exceptions)
ALLOWED_PATTERNS = [
    r'diagram\.get_nodes_by_type\(.*\)\s+or\s+diagram\.nodes',  # Fallback pattern
    r'all_nodes.*=.*diagram\.get_nodes_by_type\(.*\)\s+or\s+diagram\.nodes',  # Assignment with fallback
    r'domain_diagram\.nodes',  # DomainDiagram doesn't have query methods
    r'domain_diagram\.edges',  # DomainDiagram doesn't have query methods
]

# Files/directories to check
APPLICATION_PATHS = [
    'dipeo/application/',
]

# Files/directories to exclude from checking
EXCLUDE_PATHS = [
    'dipeo/application/diagram/use_cases/compile_diagram.py',  # Compiler needs direct access
    'dipeo/application/diagram/use_cases/validate_diagram.py',  # Validator needs direct access
]


def check_file(filepath: Path) -> List[str]:
    """Check a single file for forbidden patterns."""
    errors = []
    
    # Skip excluded files
    for exclude in EXCLUDE_PATHS:
        if str(filepath).endswith(exclude) or exclude in str(filepath):
            return errors
    
    try:
        content = filepath.read_text()
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
            
            # Check if line matches any allowed pattern
            is_allowed = False
            for allowed_pattern in ALLOWED_PATTERNS:
                if re.search(allowed_pattern, line):
                    is_allowed = True
                    break
            
            if is_allowed:
                continue
            
            # Check for forbidden patterns
            for pattern, message in FORBIDDEN_PATTERNS:
                if re.search(pattern, line):
                    errors.append(f"{filepath}:{line_num}: {message}")
                    break  # Only report first error per line
    
    except Exception as e:
        errors.append(f"{filepath}: Error reading file: {e}")
    
    return errors


def main():
    parser = argparse.ArgumentParser(
        description='Check for direct diagram internal access patterns'
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='Files to check (if empty, checks all application files)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Suggest fixes for found issues'
    )
    
    args = parser.parse_args()
    
    # Determine files to check
    files_to_check = []
    if args.files:
        files_to_check = [Path(f) for f in args.files if f.endswith('.py')]
    else:
        # Check all Python files in application paths
        for app_path in APPLICATION_PATHS:
            path = Path(app_path)
            if path.exists():
                files_to_check.extend(path.rglob('*.py'))
    
    # Check each file
    all_errors = []
    for filepath in files_to_check:
        errors = check_file(filepath)
        all_errors.extend(errors)
    
    # Report results
    if all_errors:
        print("❌ Found direct diagram access patterns:\n")
        for error in all_errors:
            print(f"  {error}")
        
        if args.fix:
            print("\n💡 Suggested fixes:")
            print("  - Use diagram.get_incoming_edges(node_id) instead of filtering diagram.edges")
            print("  - Use diagram.get_outgoing_edges(node_id) instead of filtering diagram.edges")
            print("  - Use diagram.get_nodes_by_type(NodeType) instead of filtering diagram.nodes")
            print("  - Use diagram.get_node(node_id) for single node lookup")
            print("  - Use diagram.get_start_nodes() for start nodes")
        
        return 1
    else:
        print("✅ No direct diagram access patterns found")
        return 0


if __name__ == '__main__':
    sys.exit(main())